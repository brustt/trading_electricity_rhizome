import pandas as pd
import glob
import os
from src.constants import PATH_DATA_PROCESSED

dict_data_name = {
    "germany": "BZN-DE-LU"
}

class DataLoader:
    def __init__(self):
        pass

    def load_dataset(self, name, start_date=None, end_date=None):
        dir_name= os.path.join(PATH_DATA_PROCESSED, dict_data_name[name])
        return self._load_dataset(dir_name)

    def _load_dataset(self, dir_name):
        data_list = []
        for file in glob.glob(dir_name+"*.xlsx"):
            data_list.append(pd.read_excel(file))

        return pd.concat(data_list).reset_index(drop=True)