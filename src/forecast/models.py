import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime
from typing import Dict, List
from src.forecast.factory import ForecastModel

# fix seed somewhere

class Dummy(ForecastModel):
    def forecast(self, n_frames):
        return None
    
    def train_model(self, x_train):
        return None


class ARIMAModel(ForecastModel):
    def __init__(self,
                 order:Dict[str, int],
                seasonal_order:float = None):
        
        self.order = order
        self.seasonal_order = seasonal_order
        
    def forecast(self, n_frames):
        return self.model.forecast(steps=n_frames)
    
    def train_model(self, x_train):
        self.model = ARIMA(
            endog=x_train, 
            order=(self.order["p"], self.order["d"], self.order["q"]), 
            freq='H', 
            seasonal_order=self.seasonal_order).fit()