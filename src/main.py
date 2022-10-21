from dataclasses import dataclass, field
from typing import Dict
from src.action_strategy.factory import ActionStrategy
from src.action_strategy.mean_reversion import MeanReversion
from src.forecast.factory import ModelForecastFactory
from src.forecast.runner import ForecastRunner
from src.forecast.utils import SamplerSetForecast
from src.io.load import DataLoader, load_config
from src.io.save import Dumper
from src.preprocessing.preprocess import ProcessData
from src.stock import Balance, Stock
import pandas as pd
import logging
from src.trade_manager import TradeManagerV0
from datetime import datetime
import math
logging.basicConfig()
log=logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def load_data(name="germany"):
    builder = DataLoader()
    return builder.load_dataset(name, start_date=None, end_date=None)

def dummy_func():
    log.info("here there")

@dataclass
class Experiment:
    """ run experiment"""
    stock: Stock
    df: pd.DataFrame
    forecast_runner: ForecastRunner
    strategy: ActionStrategy
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
            )
        self.manager = TradeManagerV0(strategy=self.strategy,
                                forecast_runner=self.forecast_runner,
                                     )

        for _ in range(1, self.config_exp["n_iteration"]+1):
            self.manager.strategy.get_indicator(
                x_train=self.forecast_runner.sampler.x_train,
                x_test=self.forecast_runner.sampler.x_test
            )
            results_window.append(self.run_window())
            self.forecast_runner.sampler.resample_train_test_set()

        self.df_results  = pd.concat(results_window, axis=0)

    def run_window(self):
        results = self.manager.run_trade(self)
        log.info("window done")
        return results





if __name__=="__main__":

    config_file = "1"
    # Load config and data
    logging.info("Load data and config..")
    config_exp = load_config(config_file)
    prices = load_data(config_exp["market_name"])
    config_exp["date_start"] =  datetime.strptime(' '.join([config_exp["date_start"], config_exp["hour_begin_trade"]]), "%d-%m-%Y %H")
    config_exp["date_end"] =  datetime.strptime(' '.join([config_exp["date_end"], config_exp["hour_begin_trade"]]), "%d-%m-%Y %H")

    n_days = (config_exp["date_end"] - config_exp["date_start"]).days
    config_exp["n_iteration"] = math.ceil(n_days/config_exp["n_frames"])
    
    logging.info("Process data ..")
    prices = ProcessData(df=prices).run_preprocess()
    prices = prices.to_frame("value")


    # Init classes
    logging.info("Init classes..")

    stock = Stock(storage_pwr=config_exp["storage_pwr"], 
                    rho_d=config_exp["rho_d"], 
                    rho_s=config_exp["rho_s"],
                    t_discharge=config_exp["t_discharge"],
                    init_storage_cpty=config_exp["init_storage_cpty"],
                    )

    balance = Balance(init_level=config_exp["balance_init_level"])

    # sampler for train and test sets
    sampler = SamplerSetForecast(df=prices, 
                                n_frames=config_exp["n_frames"],
                                )
    # init forecast model
    model_forecast = ModelForecastFactory().get_model(**{
                                            "name":"arima",
                                            "order":dict(p=24, d=1, q=0),
                                            "seasonal_order":None,
                                            })
    logging.info("Init forecast runner..")

    # forecast prices run
    forecast_runner = ForecastRunner(model=model_forecast,
                                    n_frames=config_exp["n_frames"],
                                    sampler=sampler,
                                    )    
    # trading strategy
    strategy = MeanReversion(prices=prices,
                            period=config_exp["period"],
                            alpha=config_exp["alpha"],
                            )

    exp = Experiment(stock=stock, 
                    df=sampler.df,
                    forecast_runner=forecast_runner,
                    strategy=strategy,
                    balance=balance,
                    config_exp=config_exp,
                    )

    # run experience
    exp.run()

    # get results
    df_prices_indicators = exp.df_results
    df_prices_indicators.index = list(map(str, df_prices_indicators.index))
    history_flow_money = pd.DataFrame(
        exp.balance.history, 
        columns=["true_prices", "price_flow", "action", "current_balance"], 
        index=list(map(str, df_prices_indicators.index)))

    history_flow_energy = pd.DataFrame(
        exp.stock.history, 
        columns=["energy_trade", "current_cpty"],
        index=list(map(str, df_prices_indicators.index)))

    df_prices_indicators = df_prices_indicators[["mean", "std", "upper_bollinger", "lower_bollinger", "pred_prices"]]
    df_resume = pd.concat([
        history_flow_money,
        history_flow_energy,
        df_prices_indicators,
    ], axis=1)
    print(df_resume)

    # export results (xlsx)
    folder_exp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = "_".join(["results", folder_exp])
    dumper = Dumper(folder_name=folder_exp).save(df_resume, file_name=file_name)