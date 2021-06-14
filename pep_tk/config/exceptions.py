class MissingPortsException(Exception):
    def __init__(self, ports, dataset_name):
        self.ports = ports
        self.dataset_name = dataset_name
        self.message = 'This pipeline requires %s, which was not defined in the dataset %s.' % (str(self.ports), self.dataset_name)

        super().__init__(self.message)

class InvalidConfigOptionDefaultException(Exception):
    def __init__(self, group, name, default):
        self.group = group
        self.name = name
        self.default = default
        self.message = 'Config %s:%s has default defined as %s which is invalid.' % \
                       (self.group, self.name, str(self.default))
        super().__init__(self.message)

class InvalidConfigOptionTypeException(Exception):
    def __init__(self, category, name, type):
        self.category = category
        self.name = name
        self.type = type
        self.message = 'Config %s:%s type %s invalid.' % (self.category, self.name, self.type)
        super().__init__(self.message)

class MissingConfigGroupException(Exception):
    def __init__(self, group_name):
        self.group_name = group_name
        self.message = 'Config group is required and is not defined.' % (self.group_name)
        super().__init__(self.message)