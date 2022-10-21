from dataclasses import dataclass
from unicodedata import name
import pandas as pd
import glob
import os
from src.constants import RESULTS_PATH

@dataclass
class Dumper:
    folder_name: str

    def save(self, df_results, file_name="results"):
        name_folder = os.path.join(RESULTS_PATH, self.folder_name)
        if not os.path.exists(name_folder):
            os.mkdir(name_folder)
        name_file = os.path.join(name_folder, file_name)
        df_results.to_excel(''.join([name_file, '.xlsx']))

