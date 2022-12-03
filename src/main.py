import logging
from datetime import datetime

import click

from src.experiment import Experiment, init_experiment_classes
from src.io.load import load_config, load_data
from src.io.save import save_results

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


@click.command()
@click.option("--market_name", default="germany", help="market to trade")
@click.option("--exp_name", default="", help="exp_name")
def run_trading(market_name, exp_name):

    exp_name = "_".join([exp_name, market_name])
    config_file = "1"
    # Load config and data
    log.info("Load data and config..")
    config_exp = load_config(config_file)
    config_exp["market_name"] = market_name

    log.info(f"""LET'S TRADE ON {config_exp["market_name"]}""")
    config_exp["date_start"] = datetime.strptime(
        " ".join([config_exp["date_start"], config_exp["hour_begin_trade"]]),
        "%d-%m-%Y %H",
    )
    config_exp["date_end"] = datetime.strptime(
        " ".join([config_exp["date_end"], config_exp["hour_begin_trade"]]),
        "%d-%m-%Y %H",
    )

    config_exp["n_iteration"] = (config_exp["date_end"] - config_exp["date_start"]).days

    prices = load_data(config_exp["market_name"], end_year=config_exp["date_end"])

    # Init classes
    log.info("Init classes..")
    stock, balance, sampler, forecast_runner, strategy = init_experiment_classes(
        prices, config_exp
    )

    exp = Experiment(
        exp_name=exp_name,
        stock=stock,
        df=sampler.df,
        forecast_runner=forecast_runner,
        strategy=strategy,
        balance=balance,
        config_exp=config_exp,
    )

    # run experience
    exp.run()
    
    # save exp
    save_results(exp)


if __name__ == "__main__":

    run_trading()
