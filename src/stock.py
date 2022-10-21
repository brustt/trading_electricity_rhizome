from dataclasses import dataclass, field
import pandas as pd
import numpy as np
import logging
from src.action_strategy.factory import TradeAction
log=logging.getLogger(__name__)
log.setLevel('INFO')


@dataclass
class Stock:
    storage_pwr: float
    rho_d: float
    rho_s: float
    t_discharge: float
    init_storage_cpty: float
    current_cpty: float = field(init=False)
    storage_cpty: float = field(init=False)


    def __post_init__(self):
        self.init_stock()
        self.history = []

    def init_stock(self):
        self.storage_cpty = int(self.storage_pwr*(self.t_discharge/self.rho_d))
        self.current_cpty = self.init_storage_cpty
    
    def update_stock(self, action: str):
        """
        we have equivalence in energy trade unit bewteen what we give to market
        """
        
        log.info("========")
        log.info(f"action Stock : {action}")
        qty=0
        if action == TradeAction.BUY.name:
            qty = self.add_to_stock()
        elif action == TradeAction.SELL.name:
            qty = self.retrieve_from_stock()
        log.info(f"Updated Stock : {self.current_cpty}")
        self.history.append((qty, self.current_cpty,))
        return qty

    @property
    def is_empty(self):
        return self.current_cpty == 0
    
    @property
    def is_full(self):
        return self.current_cpty == self.storage_cpty

    def add_to_stock(self):
        qty = (
            min(
                (self.storage_cpty - self.current_cpty), 
                (self.storage_pwr*self.rho_s*1)
            )
        if not self.is_full else 0.)
        log.info(f'current : {self.current_cpty} - action qty : {qty}')
        self.current_cpty += qty

        # flow is what energy is bought from market : coef for price (negative)

        # normal buy - add rho_s*qty to stock but bought self.storage_pwr*1
        if (qty/self.rho_s/1 == self.storage_pwr):
            flow = -self.storage_pwr*1
        else:
        # almost full; to add cpty we need to buy qty/rho_s
            flow = -qty/self.rho_s

        return flow

    def retrieve_from_stock(self):
        qty = (
            min(
                self.current_cpty, 
                (self.storage_pwr/self.rho_d*1)
            )
        if not self.is_empty else 0.)
        log.info(f'current : {self.current_cpty} - action qty : -{qty}')
        self.current_cpty -= qty

        # flow is what energy is given to market : coef for price (positive)

        # normal sell : we retrieve
        if (qty*self.rho_d/1 == self.storage_pwr):
            # flow to market after rho_d
            flow = self.storage_pwr*1
        else:
            # almost empty we give to market what we can : qty*rho_d
            flow = qty*self.rho_d

        return flow


@dataclass
class Balance:
    init_level: float

    def __post_init__(self):
        self.init_balance()

    def init_balance(self):
        self.current_level = self.init_level
        self.history = []

    def update_balance(self, action: str, price: float, flow: float):
        # check if stock was updated
        self.current_level += price*flow
        action = action if flow !=0 else (f"HOLD_{action[0].lower()}") if action != "HOLD" else "HOLD"
        self.history.append((price, price*flow, action, self.current_level,))
        return self