from datetime import datetime
from typing import Dict

from src.datasets import VIAMEDataset

ENV_VARIABLE = str
VALUE = str

class DatasetEnvPorts:
    def __init__(self, config):
        self.__config = config

    def get_env_ports(self, dataset: VIAMEDataset, missing_ok = False) -> Dict[ENV_VARIABLE, VALUE]:
        res = {}
        for name, attributes in self.__config.items():
            attr = attributes['dataset_attribute']
            if not missing_ok and not attr in dataset.attributes:
                msg = 'This pipeline requires %s, which was not defined in the dataset %s.' % (attr, dataset.dataset_name)
                raise Exception(msg)

            if not attr in dataset.attributes:
                continue

            res[attributes['env_variable']] = dataset.attributes[attr]
        return res

