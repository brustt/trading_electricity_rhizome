from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List
import pandas as pd
import logging
from src.action_strategy.factory import ActionStrategy
from src.forecast.runner import ForecastRunner
from src.stock import Balance, Stock

log=logging.getLogger(__name__)
log.setLevel(logging.INFO)

@dataclass
class TradeManagerV0:
    strategy: ActionStrategy
    forecast_runner: ForecastRunner

    def trade_on_period(self):
        pass

    def run_trade(self, exp):
        self.forecast_runner.run_training()
        pred_prices = self.forecast_runner.run_forecast()
        pred_prices = pred_prices.to_frame("value")
        results = self.strategy.get_action_window(pred_prices)

        for _, s_price in results.iterrows():
            self.trade_unit(s_price, exp)
        
        return results
        
    def trade_unit(self, s_price: pd.Series, exp):

        flow = exp.stock.update_stock(s_price['action'])

        exp.balance.update_balance(action=s_price['action'], 
                                price=s_price['true_prices'],
                                flow=flow,
                                )

        log.info(f"Current cpty : {exp.stock.current_cpty}")
        log.info(f"Current balance : {exp.balance.current_level}")
