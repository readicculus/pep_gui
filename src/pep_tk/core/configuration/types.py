#      This file is part of the PEP GUI detection pipeline batch running tool
#      Copyright (C) 2021 Yuval Boss yuval@uw.edu
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os

import re

class ConfigType:
    def __init__(self, var_type):
        self.var_type = var_type

    def validate(self, text):  raise NotImplementedError('ConfigType: Must implement validate')

    def description(self): raise NotImplementedError('ConfigType: Must implement description')

class StringType(ConfigType):
    def __init__(self):
        ConfigType.__init__(self, var_type=str)

    def validate(self, text):
        return True, text

    def description(self): return 'text'

class ConfigIntType(ConfigType):
    def __init__(self, min, max):
        ConfigType.__init__(self, var_type=int)
        self.min = min
        self.max = max

    def validate(self, text):
        text = str(text)
        if not text.isdigit():
            return False, text
        try:
            text = self.var_type(text)
        except:
            return False, text
        if not self.min is None and text < self.min:
            return False, text
        if not self.max is None and text > self.max:
            return False, text
        return True, text

    def description(self):
        if self.min is not None and self.max is not None: return 'integer between %d and %d' % (self.min, self.max)
        if self.min is None and self.max is not None: return 'integer less than %d' % self.max
        if self.max is None and self.min is not None: return 'integer greater than %d' % self.min
        return 'integer'

class ConfigFloatType(ConfigType):
    def __init__(self, min, max):
        ConfigType.__init__(self, var_type=float)
        self.min = min
        self.max = max

    def validate(self, text):
        try:
            text = self.var_type(text)
        except:
            return False, text
        if not self.min is None and text < self.min:
            return False, text
        if not self.max is None and text > self.max:
            return False, text
        return True, text

    def description(self):
        if self.min is not None and self.max is not None: return 'decimal between %.1f and %.1f' % (self.min, self.max)
        if self.min is None and self.max is not None: return 'decimal less than %.1f' % self.max
        if self.max is None and self.min is not None: return 'decimal greater than %.1f' % self.min
        return 'decimal'

class ConfigOutputImageListType(StringType):
    def __init__(self):
        StringType.__init__(self)

    def validate(self, text):
        fp_pattern, ext = os.path.splitext(text)
        return ext=='.txt', fp_pattern

    def description(self): return 'file pattern'

class ConfigOutputDetectionsType(StringType):
    def __init__(self):
        StringType.__init__(self)

    def validate(self, text):
        fp_pattern, ext = os.path.splitext(text)
        return ext=='.csv', fp_pattern

    def description(self): return 'file pattern'


def parse_type(type_str: str):
    '''
    Parse a type
    int[]
    str
    float
    '''
    int_exp = r'^int(?:\[(\d+)\,(\d+)?\])?$'
    float_exp = r'^float(?:\[([+-]?(?:[0-9]*[.])?[0-9]+)\,([+-]?(?:[0-9]*[.])?[0-9]+)?\])?$'
    out_imagelist_exp = '^output_image_list$'
    out_detections_exp = '^output_detections_file$'
    m = re.match(int_exp, type_str)
    if m:
        groups = m.groups()
        min = int(groups[0]) if groups[0] is not None else None
        max = int(groups[1]) if groups[1] is not None else None
        return ConfigIntType(min, max)
    m = re.match(float_exp, type_str)
    if m:
        groups = m.groups()
        min = float(groups[0]) if groups[0] is not None else None
        max = float(groups[1]) if groups[1] is not None else None
        return ConfigFloatType(min, max)

    m = re.match(out_imagelist_exp, type_str)
    if m:
        return ConfigOutputImageListType()
    m = re.match(out_detections_exp, type_str)
    if m:
        return ConfigOutputDetectionsType()

    return StringType()