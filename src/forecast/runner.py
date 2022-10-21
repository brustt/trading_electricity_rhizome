from typing import List
from src.forecast.factory import ForecastModel
import pandas as pd
from src.forecast.utils import SamplerSetForecast


class ForecastRunner:
    def __init__(self,
                model: ForecastModel,
                n_frames: int,
                sampler: SamplerSetForecast,):
        self.model = model
        self.n_frames=n_frames
        self.sampler = sampler
    
    def init_sampler(self, df):
        return SamplerSetForecast(df)
    
    def run_forecast(self):
        return self.model.forecast(self.n_frames)
    
    def run_training(self):
        self.model.train_model(self.sampler.x_train)
    
    def run_sequential_window(self, n_periods):
        pred_list: List[pd.Series] = []
        self.sampler = self.init_sampler()
        for idx in range(1, (n_periods*self.n_frames)+1):
            if idx % self.frames == 0:
                self.sampler.resample_train_test_set(self.n_frames)
                self.run_training(self.sampler.x_train)
                pred_list.append(self.run_forecast(self.n_frames))
                
        return pd.concat(pred_list, axis=0)