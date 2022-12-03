import glob
import os
from datetime import datetime

import pandas as pd
import yaml
from yaml.loader import SafeLoader

from src.constants import DICT_PARAMS_PATH, PATH_DATA_PRICES


def load_data(name, end_year):
    builder = DataLoader()
    return builder.load_dataset(name, start_date=None, end_date=end_year)


class DataLoader:
    def __init__(self):
        pass

    def load_dataset(
        self, name, start_date: datetime = None, end_date: datetime = None
    ):
        dir_name = os.path.join(PATH_DATA_PRICES, name)
        prices = self._load_all_files(dir_name, end_date.year)
        # idx = pd.date_range(prices.index.min(), prices.index.max(), freq="H")
        # prices.index = pd.DatetimeIndex(prices.index)
        # prices = prices.reindex(idx, fill_value='NaN')
        return prices

    def _load_all_files(self, dir_name, max_year):
        data_list = []
        for file in glob.glob(dir_name + "/*.xlsx"):
            if int(file[:-5][-4:]) <= max_year:
                data_list.append(pd.read_excel(file, index_col=0))

        prices = pd.concat(data_list).sort_index()
        prices.index = pd.to_datetime(prices.index)
        return prices


def load_config(name_config):
    with open(DICT_PARAMS_PATH[name_config]) as f:
        return yaml.load(f, Loader=SafeLoader)
