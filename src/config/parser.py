import regex as re

from src.config.types import ConfigIntType, ConfigFloatType, parse_type

class ConfigOption():
    def __init__(self, name, default, type, value=None):
        self.name = name
        self.default = default
        self.__value = value
        self.validator = parse_type(type)

    def value(self):
        if self.__value:
            return self.__value
        return self.default

    def set_value(self, value):
        valid, res = self.validator.validate(value)
        if valid:
            self.__value = res
            return True
        return False

    def reset(self):
        self.__value = self.default

class PipelineGlobalConfig:
    def __init__(self, config):
        self.__config = {}

        for name, attributes in config.items():
            o = ConfigOption(name, attributes.get('default'), attributes.get('type'))
            self.__config[name] = o

    def get_config(self):
        return self.__config

    def get_config_option(self, name):
        return self.__config.get(name)

    def set_config_option(self, name, value):
        opt = self.__config.get(name)
        if opt == None:
            return False

        return opt.set_value(value)

    def reset_config_option(self, name):
        opt = self.__config.get(name)
        opt.reset()

    def reset_all_defaults(self):
        for name in list(self.__config.keys()):
            self.reset_config_option(name)

    def __len__(self):
        return len(self.__config)

    def  __getitem__(self, name):
        return self.get_config_option(name)