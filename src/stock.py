import logging
from dataclasses import dataclass, field

from src.action_strategy.abstract_models import TradeAction

log = logging.getLogger(__name__)
log.setLevel("INFO")

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
    
    def update_stock(self, action: str, flow:float=None):
        """
        we have equivalence in energy trade unit bewteen what we give to market
        """
        #print(f"action Stock : {action}")
        qty=0
        if action == TradeAction.BUY.name:
            qty = self.add_to_stock(flow)
        elif action == TradeAction.SELL.name:
            qty = self.retrieve_from_stock(flow)
        log.info(f"Updated Stock : {self.current_cpty}")
        self.history.append((qty, self.current_cpty,))
        return qty

    @property
    def is_empty(self):
        return self.current_cpty == 0
    
    @property
    def is_full(self):
        return self.current_cpty == self.storage_cpty

    def add_to_stock(self, flow=None):
        """BUY"""
        if flow is None:
            qty = (
                min(
                    (self.storage_cpty - self.current_cpty), 
                    (self.storage_pwr*self.rho_s*1)
                )
            if not self.is_full else 0.)
            # flow is what energy is bought from market : coef for price (negative)

            # normal buy - add rho_s*qty to stock but bought self.storage_pwr*1
            if (qty/self.rho_s/1 == self.storage_pwr):
                flow = -self.storage_pwr*1
            else:
            # almost full; to add cpty we need to buy qty/rho_s
                flow = -qty/self.rho_s
        else:
            qty = min(flow*self.rho_s, (self.storage_cpty - self.current_cpty))
            flow=-flow
            
        self.current_cpty += qty
        

        return flow


    def retrieve_from_stock(self, flow=None):
        """SELL"""
        if flow is None:
            qty = (
                min(
                    self.current_cpty, 
                    (self.storage_pwr/self.rho_d*1)
                )
            if not self.is_empty else 0.)

            # flow is what energy is given to market : coef for price (positive)

            # normal sell : we retrieve
            if (qty*self.rho_d/1 == self.storage_pwr):
                # flow to market after rho_d
                flow = self.storage_pwr*1
            else:
                # almost empty we give to market what we can : qty*rho_d
                flow = qty*self.rho_d
        else:
            qty = min(flow/self.rho_d, self.current_cpty)

        
        self.current_cpty -= qty

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
        #log.info(f"ADD : {price*flow} €")
        #log.info(f"Current : { self.current_level} €")

        action = action if flow !=0 else (f"HOLD_{action[0].lower()}") if action != "HOLD" else "HOLD"
        self.history.append((price, price*flow, action, self.current_level,))
        return self