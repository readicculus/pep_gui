"""
Original: https://github.com/SzieberthAdam/jsonfile

The ``jsonfile`` Python module can be used to sync a JSON file
on a disk with the corresponding Python object instance.

Can be used to autosave JSON compatible Python data.
"""
__version__ = "0.0.9"

import collections.abc
import copy
import json
import pathlib
import tempfile


class JSONFileBase:

    @property
    def root(self):
        return self._root

    def _get_adapter_or_value(self, data):
        if isinstance(data, collections.abc.Mapping):
            return JSONFileObject(self._root, data)
        elif isinstance(data, str):
            return data
        elif isinstance(data, collections.abc.Sequence):
            return JSONFileArray(self._root, data)
        else:
            return data

    @staticmethod
    def _value_norm(value):
        if isinstance(value, (
                collections.abc.Mapping,
                JSONFileObject,
        )):
            return {str(k): v for k, v in value.items()}
            # JSON obejct keys must be strings
        elif isinstance(value, str):
            return value
        elif isinstance(value, (
                collections.abc.Sequence,
                JSONFileArray,
        )):
            return list(value)
        else:
            return value


class JSONFile(JSONFileBase):

    def __init__(self, filepath, *,
                 data=...,
                 default_data=...,
                 autosave=False,
                 dump_kwargs=None,
                 load_kwargs=None,
                 ):
        self._root = self
        self.changed = None
        self.default_data = default_data
        self._data = (default_data if data is ... else data)
        self.autosave = autosave
        self.dump_kwargs = dump_kwargs or dict(
            skipkeys=False,
            ensure_ascii=True,
            check_circular=True,
            allow_nan=True,
            cls=None,
            indent=None,
            separators=None,
            default=None,
            sort_keys=False,
        )
        self.load_kwargs = load_kwargs or dict(
            cls=None,
            object_hook=None,
            parse_float=None,
            parse_int=None,
            parse_constant=None,
            object_pairs_hook=None,
        )
        self.filepath = filepath
        if self._data == self.default_data:
            self.reload()
        elif autosave:
            self.save()

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.filepath}')"

    def __str__(self):
        return self.__repr__()

    @property
    def autosave(self):
        return bool(self._autosave)  # ensure boolean

    @autosave.setter
    def autosave(self, value):
        self._autosave = bool(value)  # ensure boolean

    @property
    def data(self):
        return self._get_adapter_or_value(self._data)

    @data.setter
    def data(self, value):
        if value is ...:
            raise ValueError("Ellipsis is forbidden, call delete()")
        old_data = copy.copy(self._data)
        self._data = self._value_norm(value)
        self.may_changed(self, old_data)

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, value):
        self._filepath = pathlib.Path(value)  # ensure Path instance

    def delete(self):
        # could have been @data.deleter but that would be obscure
        old_data = copy.copy(self._data)
        self._data = self.default_data
        self.may_changed(self, old_data)
        try:
            self.filepath.unlink()
        except FileNotFoundError:
            pass  # delete can happen previously

    def may_changed(self, inst, old_data):
        if inst._data != old_data:
            self.changed = True
            self.on_change()

    def on_change(self):
        # print("on change", self, self.autosave)
        if self.autosave:
            self.save()

    def reload(self):
        p = self.filepath
        if (
                p.is_file()  # filepath_exists
                and p.stat().st_size  # filepath_not_empty
        ):
            with p.open(encoding="utf8") as f:
                self._data = json.load(f, **self.load_kwargs)
                self.changed = False
        else:
            self._data = copy.deepcopy(self.default_data)
            self.changed = None

    def save(self, ensure_parents=True):
        p = self.filepath
        if self._data == self.default_data and p.is_file():
            p.unlink()
        else:
            s = json.dumps(self._data, **self.dump_kwargs)
            if ensure_parents:  # ensure parent directories
                p.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                    'w',
                    dir=p.parent,
                    delete=False,
                    encoding="utf8",
            ) as tf:
                tf.write(s)
                tp = p.parent / tf.name
            tp.replace(p)

from collections.abc import Mapping
class JSONFileContainer(JSONFileBase, Mapping):

    def __init__(self, root, data):
        self._root = root
        self._data = data

    def __contains__(self, key):  # has to be explicit
        return self._data.__contains__(key)

    def __delitem__(self, key):  # has to be explicit
        m = self._change_method("__delitem__")
        return m(key)

    def __eq__(self, other):  # has to be explicit
        return self._data.__eq__(other)

    def __dir__(self):
        return self._data.__dir__()

    @property
    def __doc__(self):
        return self._data.__doc__

    def __iter__(self):  # has to be explicit
        return self._data.__iter__()

    def __getattr__(self, name):
        return getattr(self._data, name)

    def __getattribute__(self, name):
        Ns = object.__getattribute__(self, "_change_method_names")
        if name in Ns:
            m = object.__getattribute__(self, "_change_method")
            return m(name)
        return object.__getattribute__(self, name)

    def __getitem__(self, key):
        data = self._data[key]
        return self._get_adapter_or_value(data)

    def __len__(self):
        return self._data.__len__()

    def __ne__(self, other):  # has to be explicit
        return self._data.__ne__(other)

    def __repr__(self):
        return self._data.__repr__()

    def __setitem__(self, key, value):  # has to be explicit
        m = self._change_method("__setitem__")
        return m(key, self._value_norm(value))

    def _change_method(self, name):
        def wrapped_method(*args, **kwargs):
            old_data = copy.copy(self._data)
            _data = object.__getattribute__(self, "_data")
            m = getattr(_data, name)
            try:
                r = m(*args, **kwargs)
                self._root.may_changed(self, old_data)
            except:
                self._data = old_data
                raise
            return r

        return wrapped_method


class JSONFileArray(JSONFileContainer, list):
    _change_method_names = (
        "__delitem__",
        "__iadd__",
        "__imul__",
        "__setitem__",
        "append",
        "clear",
        "extend",
        "insert",
        "pop",
        "remove",
        "reverse",
        "sort",
    )


class JSONFileObject(JSONFileContainer, dict):
    _change_method_names = (
        "__delitem__",
        "__setitem__",
        "clear",
        "pop",
        "popitem",
        # "setdefault",  # handled exceptionally
        "update",
    )

    def __setitem__(self, key, value):  # has to be explicit
        key = str(key)  # JSON obejct keys must be strings
        return super().__setitem__(key, value)

    def get(self, key, default=None):
        # avoid return of list/dict objects
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        for k in self:
            yield k, self[k]

    def setdefault(self, key, default):
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return self[key]

    def values(self):
        for k in self:
            yield self[k]

    def asdict(self):
        return self._data

jsonfile = JSONFile
