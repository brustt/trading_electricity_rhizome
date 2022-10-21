import pandas as pd
import numpy as np

class SamplerSetForecast:
    def __init__(self, 
                 df: pd.DataFrame, 
                 n_frames:int = None,
                 prop: float = 0.2,
                ):

        self.df = df
        self.n_frames = n_frames
        self.prop = prop

    def init_train_test_set(self, date_start=None, date_end=None):

        if date_start and date_end:
            self.split_train_test_set_on_date(date_start)
            self.split_idx = np.where(self.df.index == date_start)[0][0]
        else:
            self.split_idx = int((1-self.prop)*len(self.df))
            self.split_train_test_set()
    
    def split_train_test_set_on_date(self, date_start):
        self.x_train, self.x_test = self.df.loc[:date_start, 'value'], self.df.loc[date_start:, 'value']

    def split_train_test_set(self):
        self.x_train, self.x_test = self.df[:self.split_idx]['value'], self.df[self.split_idx:]['value']

    def resample_train_test_set(self):
        self.split_idx +=self.n_frames
        self.split_train_test_set()

