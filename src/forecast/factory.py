from abc import ABC, abstractmethod
from typing import List
import pandas as pd

class ModelForecastFactory:

    def get_model(self, **kwargs):
        from src.forecast.models import ARIMAModel
        name = kwargs["name"]
        choice_model = {
            "arima":{
                "builder":ARIMAModel,
                "params":[
                    "order",
                    "seasona_order",
                ]
            }
        }
        params = {k:v for k,v in kwargs.items() if k in choice_model[name]["params"]}
        return choice_model[name]["builder"](**params)

class ForecastModel(ABC):
        
    @abstractmethod
    def forecast(self, n_frames):
        pass
    
    @abstractmethod
    def train_model(self, x_train):
        pass
    
    def format_prediction(self, x_test: pd.Series, predictions: List):
        return pd.Series(predictions, index=x_test.index)