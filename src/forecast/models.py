from abc import ABC, abstractmethod
from typing import Dict, List

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from statsmodels.tsa.arima.model import ARIMA


# fix seed somewhere
class ForecastModel(ABC):
    @abstractmethod
    def forecast(self, n_frames):
        pass

    @abstractmethod
    def train_model(self, x_train):
        pass

    def format_prediction(self, x_test: pd.Series, predictions: List):
        return pd.Series(predictions, index=x_test.index)


class Dummy(ForecastModel):
    def forecast(self, n_frames):
        return None

    def train_model(self, x_train):
        return None


class ARIMAModel(ForecastModel):
    def __init__(self, order: Dict[str, int], seasonal_order: float = None):

        self.order = order
        self.seasonal_order = seasonal_order

    def forecast(self, n_frames):
        return self.model.forecast(steps=n_frames)

    def train_model(self, x_train):
        self.model = ARIMA(
            endog=x_train,
            order=(self.order["p"], self.order["d"], self.order["q"]),
            freq="H",
            seasonal_order=self.seasonal_order,
        ).fit()


class LGBMForecast(ForecastModel):
    def __init__(self, **params):
        # change here - dirty fix
        self.params = params if params else []
        self.model = LGBMRegressor(**self.params) if self.params else LGBMRegressor(random_state=12)

    def forecast(self, n_frames, sampler):
        x_test_window = sampler.x_test[:n_frames]
        x_input = sampler.x_test[:n_frames].iloc[0].values
        pred_day = []

        for _ in range(0, n_frames):
            if _ != 0:
                lags_features = [_ for _ in x_test_window.columns if _.startswith("t_")]
                other_columns = [
                    _ for _ in x_test_window.columns if _ not in lags_features
                ]

                tmp_lags = x_test_window[lags_features].iloc[_].values
                tmp_static = x_test_window[other_columns].iloc[_].values

                # we replace past day prices with forecasted ones
                tmp_lags[:_] = pred_day[::-1][:_]

                x_input = np.concatenate((tmp_lags, tmp_static), axis=0)

            last_pred = self.model.predict(x_input.reshape(1, -1))

            pred_day.append(last_pred[0])

        prices = pd.concat(
            [
                pd.Series(pred_day, index=x_test_window.index, name="pred"),
                sampler.y_test[:n_frames],
            ],
            axis=1,
        ).rename({"value": "true_prices", "pred": "value"}, axis=1)
        return prices

    def train_model(self, x_train, y_train):
        self.model.fit(x_train, y_train)
