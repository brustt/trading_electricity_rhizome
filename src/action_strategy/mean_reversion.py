from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.action_strategy.abstract_models import ActionStrategy, trade_action


class MeanReversion(ActionStrategy):
    def __init__(self, prices: pd.Series, period: int, alpha: float, column_to_trade:str,  **kwargs):
        self.prices = prices
        self.period = period
        self.alpha = alpha
        self.column_to_trade = "value" if column_to_trade == "pred" else "true_prices"

        self.kwargs = kwargs

    def get_indicator(self, x_train, x_test):
        """bollinger bands
        change to history prices and forecast
        """
        # get true prices indicator
        # value is true in x_train/x_test but pred in pred_prices
        self.prices = pd.DataFrame(
            pd.concat([x_train, x_test], axis=0), columns=["value"]
        ).rename({"value":"true_prices"}, axis=1)

        self.prices["mean"] = (
            self.prices["true_prices"].rolling(self.period, min_periods=1).mean()
        )
        self.prices["std"] = (
            self.prices["true_prices"].rolling(self.period, min_periods=1).std()
        )

        self.prices["upper_bollinger"] = self.prices["mean"] + (
            self.alpha * self.prices["std"]
        )
        self.prices["lower_bollinger"] = self.prices["mean"] - (
            self.alpha * self.prices["std"]
        )

    def trade_on_window(
        self, window_prices: pd.DataFrame, stock, balance
    ) -> pd.DataFrame:

        # tmp workaround
        self.prices = self.prices[~self.prices.index.duplicated(keep="first")]

        window_prices["buy"] = np.where(
            window_prices[self.column_to_trade]
            <= self.prices.loc[window_prices.index, "lower_bollinger"],
            1,
            0,
        )
        window_prices["sell"] = np.where(
            window_prices[self.column_to_trade]
            >= self.prices.loc[window_prices.index, "upper_bollinger"],
            -1,
            0,
        )
        window_prices["action"] = (
            window_prices[["buy", "sell"]].sum(axis=1).map(trade_action)
        )

        window_prices = window_prices.rename({"value": "pred_prices"}, axis=1)
        true_prices = self.prices.loc[window_prices.index].drop(["true_prices"], axis=1)
        results = pd.concat([true_prices, window_prices], axis=1)
        results["flow"] = None

        return results


@dataclass
class Indicator:
    """rolling mean"""
