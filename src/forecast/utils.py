from datetime import datetime

import numpy as np
import pandas as pd


class ForecastFeatureDummy:
    def create_features(self, df):
        return df


class SamplerSetForecast:
    def __init__(
        self,
        df: pd.DataFrame,
        n_frames: int = None,
        prop: float = 0.2,
    ):

        self.df = df
        self.n_frames = n_frames
        self.prop = prop

    def init_train_test_set(
        self,
        date_start: datetime = None,
        date_end: datetime = None,
        size_window_train=730,
    ):

        self.start_train_date = date_start - pd.Timedelta(days=size_window_train)
        # self.df["day_dt"] = list(map(lambda x: x.strftime("%Y-%m-%d"), self.df.index))
        try:
            self.start_train_idx = np.where(self.df.index == self.start_train_date)[0][
                0
            ]
        except:
            self.start_train_idx = np.where(
                self.df.index == (date_start - pd.Timedelta(days=size_window_train - 7))
            )[0][0]

        if date_start and date_end:
            self.split_train_test_set_on_date(date_start)
            self.split_idx = np.where(self.df.index == date_start)[0][0]
        else:
            self.split_idx = int((1 - self.prop) * len(self.df))
            self.split_train_test_set()

    def split_train_test_set_on_date(self, date_start):
        self.x_train, self.x_test = (
            self.df.loc[self.start_train_date : date_start, :].drop("value", axis=1),
            self.df.loc[date_start:, :].drop("value", axis=1),
        )
        self.y_train, self.y_test = (
            self.df.loc[self.start_train_date : date_start, "value"],
            self.df.loc[date_start:, "value"],
        )

    def split_train_test_set(self):
        self.x_train, self.x_test = (
            self.df[self.start_train_idx : self.split_idx].drop("value", axis=1),
            self.df[self.split_idx :].drop("value", axis=1),
        )
        self.y_train, self.y_test = (
            self.df[self.start_train_idx : self.split_idx]["value"],
            self.df[self.split_idx :]["value"],
        )

    def resample_train_test_set(self):
        self.split_idx += self.n_frames
        self.split_train_test_set()


class ForecastFeatureLGBM:
    def __init__(self, **params):
        self.n_frames = params["n_frames"]
        self.n_lags_features = params["n_lags_features"]

    def create_features(self, df):
        # self.create_temporality_features()
        df = self.create_lagged_prices_feature(df)
        return df.dropna()

    def create_temporality_features(self, df):
        # add season flag
        df["month"] = df.index.month
        df = self.create_weekend_feature(df)
        df = self.create_hour_feature(df)
        return df

    def create_weekend_feature(self, df):
        df["week_day"] = df.index.day_of_week + 1
        df["weekend"] = np.where(df["week_day"].isin([6, 7]), 1, 0)
        return df.drop("week_day", axis=1)

    def create_lagged_prices_feature(self, df):
        for i in range(1, self.n_lags_features + 1):
            df["t_{}".format(i)] = df["value"].shift(i)
        return df

    def create_hour_feature(self, df):
        df["hour"] = df.index.hour
        df["hour_sin"] = np.sin(df["hour"] / 23 * 2 * np.pi)
        df["hour_cos"] = np.cos(df["hour"] / 23 * 2 * np.pi)
        return df.drop(columns="hour")
