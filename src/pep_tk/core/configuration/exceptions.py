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