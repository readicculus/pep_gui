from src.config.types import parse_type

class ConfigOption():
    def __init__(self, name, default, type, env_variable, description=None, value=None):
        self.name = name
        self.default = default
        self.__value = value
        self.validator = parse_type(type)
        self.env_variable = env_variable
        self.description = description

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
            o = ConfigOption(name, attributes.get('default'), attributes.get('type'), attributes.get('env_variable'), attributes.get('description'))
            self.__config[name] = o

    def get_config(self):
        return self.__config

    def get_config_option(self, name):
        return self.__config.get(name)

    def set_config_option(self, name, value) -> bool:
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

    def  __getitem__(self, name) -> ConfigOption:
        return self.get_config_option(name)

    # def __setattr__(self, k, v):
    #     self.data[k] = v
    #
    # def __getattr__(self, k) -> ConfigOption:
    #     # we don't need a special call to super here because getattr is only
    #     # called when an attribute is NOT found in the instance's dictionary
    #     try:
    #         return self.data[k]
    #     except KeyError:
    #         raise AttributeError