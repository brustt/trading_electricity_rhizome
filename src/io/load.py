import pandas as pd
import glob
import os
import yaml
from yaml.loader import SafeLoader

from src.constants import DICT_DATA_PATH, DICT_PARAMS_PATH, PATH_DATA_PROCESSED


class DataLoader:
    def __init__(self):
        pass

    def load_dataset(self, name, start_date=None, end_date=None):
        dir_name= os.path.join(PATH_DATA_PROCESSED, DICT_DATA_PATH[name])
        return self._load_all_files(dir_name)

    def _load_all_files(self, dir_name):
        data_list = []
        for file in glob.glob(dir_name+"*.xlsx"):
            data_list.append(pd.read_excel(file))

        return pd.concat(data_list).reset_index(drop=True)



def load_config(name_config):
    with open(DICT_PARAMS_PATH[name_config]) as f:
        return yaml.load(f, Loader=SafeLoader)
