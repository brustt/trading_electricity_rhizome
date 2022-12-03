from src.action_strategy.mean_reversion import MeanReversion
from src.action_strategy.pair_method import PairMethod


class StrategyFactory:
    def get_strategy(self, **kwargs):

        name_strategy = kwargs["name_strategy"]
        choice_strategy_builder = {
            "mean_reversion": {"builder": MeanReversion, "params": []},
            "pair_method": {"builder": PairMethod, "params": []},
        }
        return choice_strategy_builder[name_strategy]["builder"](**kwargs)
