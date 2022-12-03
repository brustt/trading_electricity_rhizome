import logging
from dataclasses import dataclass

import pandas as pd

from src.action_strategy.abstract_models import ActionStrategy
from src.forecast.runner import ForecastRunner

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class TradeManagerV0:
    strategy: ActionStrategy
    forecast_runner: ForecastRunner

    def trade_on_period(self):
        pass

    def run_trade(self, exp):
        log.info(f"\n\n ===== {self.forecast_runner.sampler.x_test.index[0]} ===== \n")
        self.strategy.get_indicator(
            x_train=self.forecast_runner.sampler.y_train,
            x_test=self.forecast_runner.sampler.y_test,
        )
        self.forecast_runner.run_training()
        pred_prices = self.forecast_runner.run_forecast()
        results = self.strategy.get_action_window(pred_prices, exp.stock, exp.balance)
        for _, s_price in results.iterrows():
            self.trade_unit(s_price, exp)
        return results

    def trade_unit(self, s_price: pd.Series, exp):
        # add qty
        flow = exp.stock.update_stock(s_price["action"], s_price["flow"])

        exp.balance.update_balance(
            action=s_price["action"],
            price=s_price["true_prices"],
            flow=flow,
        )

        log.info(f"Current cpty : {exp.stock.current_cpty}")
        log.info(f"Current balance : {exp.balance.current_level}")
