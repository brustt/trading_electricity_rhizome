from abc import ABC
from enum import Enum, auto


class TradeAction(Enum):
    BUY = auto()
    SELL = auto()
    HOLD = auto()


trade_action = {
    1: TradeAction.BUY.name,
    0: TradeAction.HOLD.name,
    -1: TradeAction.SELL.name,
}


class ActionStrategy(ABC):
    @property
    def buy(self):
        return TradeAction.BUY

    @property
    def sell(self):
        return TradeAction.SELL

    @property
    def hold(self):
        return TradeAction.HOLD
