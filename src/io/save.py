import os
from dataclasses import dataclass
from datetime import datetime
import logging
import yaml


import pandas as pd

from src.constants import RESULTS_PATH

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


@dataclass
class Dumper:
    folder_name: str

    def __post_init__(self):
        self.name_folder = os.path.join(RESULTS_PATH, self.folder_name)
        if not os.path.exists(self.name_folder):
            os.mkdir(self.name_folder)

    def save_resume(self, df_results, file_name="results"):
        name_file = os.path.join(self.name_folder, file_name)
        df_results.to_excel("".join([name_file, ".xlsx"]))

    def save_params(self, exp_params, file_name):
        name_file = os.path.join(self.name_folder, file_name)
        with open(name_file+'.yml', 'w') as f_out:
            yaml.dump(exp_params, f_out, default_flow_style=False)


def save_results(exp):
    # get results
    df_prices_indicators = exp.df_results
    df_prices_indicators.index = list(map(str, df_prices_indicators.index))
    df_prices_indicators = df_prices_indicators.rename({"value": "pred_prices"}, axis=1)
    list_dfs = []

    # history_flow_money
    list_dfs.append(
        pd.DataFrame(
            exp.balance.history,
            columns=["true_prices", "price_flow", "action", "current_balance"],
            index=list(map(str, df_prices_indicators.index)),
        )
    )

    # history_flow_energy
    list_dfs.append(
        pd.DataFrame(
            exp.stock.history,
            columns=["energy_trade", "current_cpty"],
            index=list(map(str, df_prices_indicators.index)),
        )
    )

    if exp.strategy.kwargs.get("name_strategy") == "mean_reversion":
        list_dfs.append(
            df_prices_indicators[
                ["mean", "std", "upper_bollinger", "lower_bollinger", "pred_prices"]
            ]
        )
    elif exp.strategy.kwargs.get("name_strategy") == "pair_method":
        list_dfs.append(df_prices_indicators[["pred_prices"]])

    df_resume = pd.concat(list_dfs, axis=1)
    print(df_resume)

    # export results (xlsx)
    folder_exp = "_".join([exp.exp_name, datetime.now().strftime("%Y%m%d_%H%M%S")])
    file_name = "_".join(["results", folder_exp])
    
    dumper = Dumper(folder_name=folder_exp)
    dumper.save_resume(df_resume, file_name=file_name)
    dumper.save_params(exp.config_exp, file_name=file_name)

    log.info(f"Save exp : {folder_exp}")