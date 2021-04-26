import regex as re

class ConfigType:
    def __init__(self, var_type):
        self.var_type = var_type

    def validate(self, text):  raise NotImplementedError('Must implement validate')

class StringType(ConfigType):
    def __init__(self):
        ConfigType.__init__(var_type=str)

    def validate(self, text):
        return True, text

class ConfigIntType(ConfigType):
    def __init__(self, min, max):
        ConfigType.__init__(self, var_type=int)
        self.min = min
        self.max = max

    def validate(self, text):
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

def parse_type(type_str):
    '''
    Parse a type
    int[]
    str
    float
    '''
    int_exp = '^int(?:\[(\d+)\,(\d+)?\])?$'
    float_exp = '^float(?:\[([+-]?(?:[0-9]*[.])?[0-9]+)\,([+-]?(?:[0-9]*[.])?[0-9]+)?\])?$'
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

    return StringType()