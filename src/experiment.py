import logging
from dataclasses import dataclass, field
from typing import Dict, Tuple

import pandas as pd

from src.action_strategy.factory import StrategyFactory
from src.forecast.factory import ForecastFeatureFactory, ModelForecastFactory
from src.forecast.runner import ForecastRunner
from src.forecast.utils import SamplerSetForecast
from src.stock import Balance, Stock
from src.trade_manager import TradeManagerV0

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def init_experiment_classes(prices:pd.DataFrame, config_exp: Dict) -> Tuple:

    config_exp["prices"] = prices.copy()
    log.info(f"""Process data .. {config_exp["prices"].shape}""")
    # add to experiment
    prices = ForecastFeatureFactory().get_feature_builder(
        config_exp["prices"], **config_exp["params"]
    )

    stock = Stock(
        storage_pwr=config_exp["storage_pwr"],
        rho_d=config_exp["rho_d"],
        rho_s=config_exp["rho_s"],
        t_discharge=config_exp["t_discharge"],
        init_storage_cpty=config_exp["init_storage_cpty"],
    )

    balance = Balance(init_level=config_exp["balance_init_level"])

    # sampler for train and test sets
    sampler = SamplerSetForecast(
        df=prices,
        n_frames=config_exp["n_frames"],
    )
    # init forecast model
    model_forecast = ModelForecastFactory().get_model(name=config_exp["model_name"])
    logging.info("Init forecast runner..")

    # forecast prices run
    forecast_runner = ForecastRunner(
        model=model_forecast,
        n_frames=config_exp["n_frames"],
        sampler=sampler,
    )
    # trading strategy
    strategy = StrategyFactory().get_strategy(**config_exp)
    log.info(f"STRATEGY : {config_exp['name_strategy']}")
    
    return (stock, balance, sampler, forecast_runner, strategy)


@dataclass
class Experiment:
    """run experiment"""

    exp_name: str
    stock: Stock
    df: pd.DataFrame
    forecast_runner: ForecastRunner
    strategy: any
    balance: Balance
    config_exp: Dict
    df_results: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.df_results = None

    def run(self):

        results_window = []
        self.forecast_runner.sampler.init_train_test_set(
            date_start=self.config_exp["date_start"],
            date_end=self.config_exp["date_end"],
            size_window_train=self.config_exp["size_window_train"],
        )
        self.manager = TradeManagerV0(
            strategy=self.strategy,
            forecast_runner=self.forecast_runner,
        )
        log.info(f"""N ITERATIONS {self.config_exp["n_iteration"]}""")
        for _ in range(0, self.config_exp["n_iteration"] + 1):

            results_window.append(self.run_window())
            self.forecast_runner.sampler.resample_train_test_set()
            print(results_window)
        self.df_results = pd.concat(results_window, axis=0)

    def run_window(self):
        results = self.manager.run_trade(self)
        log.info("---- day done ----")
        return results
