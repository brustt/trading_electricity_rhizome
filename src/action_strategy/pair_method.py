import copy
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.action_strategy.abstract_models import ActionStrategy, TradeAction

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.CRITICAL)


@dataclass
class Price:
    idx: int
    value: float
    type_order: str


class CheckOrderValidity:
    """check validity order
    - sequential daily order found
    - return idx's day when stock is full or empty
    """

    def __init__(self):
        pass

    def trade_unit(self, s_price: pd.Series, stock, balance):
        # print("----------")
        # print(f"IDX {s_price.name}")
        flow = stock.update_stock(s_price["action"], s_price["flow"])

        balance.update_balance(
            action=s_price["action"],
            price=s_price["true_prices"],
            flow=flow,
        )
        return flow, balance, stock

    def check_orders_validty(self, orders, stock, balance):
        flows = []
        stock_c, balance_c = copy.deepcopy(stock), copy.deepcopy(balance)

        orders["true_prices"] = orders["value"]
        # print("\n ==== Validity Check ====")
        for idx, s_price in orders.iterrows():
            # print(f"=== {_} ===")
            # print(f"Current cpty : {stock_c.current_cpty}")
            # print(f"Current balance : {balance_c.current_level}")

            flow, balance_c, stock_c = self.trade_unit(s_price, stock_c, balance_c)
            # print(s_price['action'], flow)
            if stock_c.is_empty or stock_c.is_full:
                return (
                    dict(idx=idx, reason="empty")
                    if stock_c.is_empty
                    else dict(idx=idx, reason="full")
                )
            flows.append(flow)

        return dict(idx=idx, reason="valid")


class CheckOrderValidity:
    """check validity order
    - sequential daily order found
    - return idx's day when stock is full or empty
    """

    def __init__(self):
        pass

    def trade_unit(self, s_price: pd.Series, stock, balance):
        # print("----------")
        # print(f"IDX {s_price.name}")
        flow = stock.update_stock(s_price["action"], s_price["flow"])

        balance.update_balance(
            action=s_price["action"],
            price=s_price["true_prices"],
            flow=flow,
        )
        return flow, balance, stock

    def check_orders_validty(self, orders, stock, balance):
        flows = []
        stock_c, balance_c = copy.deepcopy(stock), copy.deepcopy(balance)

        orders["true_prices"] = orders["value"]
        #print("\n ==== Validity Check ==== \n")
        for idx, s_price in orders.iterrows():
            #print(f"=== {idx} ===")
            #print(f"Current cpty : {stock_c.current_cpty}")
            #print(f"Current balance : {balance_c.current_level}")

            flow, balance_c, stock_c = self.trade_unit(s_price, stock_c, balance_c)
            #print(s_price['action'], flow)
            if stock_c.is_empty or stock_c.is_full:
                return (
                    dict(idx=idx, reason="empty")
                    if stock_c.is_empty
                    else dict(idx=idx, reason="full")
                )
            flows.append(flow)

        return dict(idx=idx, reason="valid")


class PairMethod(ActionStrategy):
    """
    Pair method strategy
    """

    def __init__(self, storage_pwr: float, rho_d: float, rho_s:float, init_storage_cpty: float, column_to_trade: str, **kwargs):
        self.unit_pwr = storage_pwr
        self.rho_d = rho_d
        self.rho_s = rho_s
        self.night_stock = init_storage_cpty
        self.validity_checker = CheckOrderValidity()
        self.column_to_trade = "value" if column_to_trade == "pred" else "true_prices"
        self.kwargs = kwargs

    def get_indicator(self, x_train=None, x_test=None):
        log.info(f"Trade on {self.column_to_trade}")
        """dummy function for TradeManager integration"""

    def trade_on_window(
        self, window_prices: pd.DataFrame, stock, balance
    ) -> pd.DataFrame:
        """deploy pair method here"""

        window_pred_prices = dict(
            zip(np.arange(0, 24), window_prices[self.column_to_trade].tolist())
        )

        current_prices = window_pred_prices.copy()
        #print(current_prices)
        it = 0

        qty = dict(zip(np.arange(0, len(current_prices)), [self.unit_pwr]*len(current_prices)))
        valid = False
        removed_prices_sell = []
        removed_prices_buy = []

        while valid is False:

            dict_res = self._pair_method_loop(current_prices, qty)
            passes_list, reason = dict_res.values()
            # if not gain at the ieme pass, we juste have to validate
            if reason == "diff" and passes_list["iteration"] == 0:
                # need to end at n-1 : already the case
                # need to validate!!
                log.info("Negative at the first pass")
                passes_list = {}
                break
            log.info(f"""PASSE OUT : {len(passes_list["passes"])}""")
            orders = self._get_action_window(passes_list, prices=window_pred_prices)

            dict_validity = self.validity_checker.check_orders_validty(
                orders, stock, balance
            )

            # check whether empty or full at ieme pass
            if dict_validity["reason"] == "empty":
                # print(f'STOCK EMPTY AT POS {dict_validity["idx"]}')
                # we search sell before buy and remove buy
                buy_idx = self.search_sBb(passes_list)
                if buy_idx is not None:
                    # reset prices
                    # print(f"sBb : {buy_idx} : {current_prices[buy_idx]}")
                    removed_prices_buy.append(buy_idx)
                    current_prices = window_pred_prices.copy()
                    current_prices = {
                        k: v
                        for k, v in current_prices.items()
                        if k not in (removed_prices_buy + removed_prices_sell)
                    }

            elif dict_validity["reason"] == "full":
                # print(f'STOCK FULL AT POS {dict_validity["idx"]}')
                # we search buy before sell and remove sell
                sell_idx = self.search_bBs(passes_list)
                if sell_idx is not None:
                    # reset prices
                    # print(f"bBs : {sell_idx} : {current_prices[sell_idx]}")
                    removed_prices_buy.append(sell_idx)
                    current_prices = window_pred_prices.copy()
                    current_prices = {
                        k: v
                        for k, v in current_prices.items()
                        if k not in (removed_prices_buy + removed_prices_sell)
                    }

            else:
                # valide
                valid = True
                # print("VALID TRADING DAY")
                # print(f"removed buy sell : {[(_,window_prices[_]) for _ in removed_prices_buy]}")
                # print(f"removed sell prices : {[(_,window_prices[_]) for _ in removed_prices_sell]}")

            it += 1

            # reset qty
            qty = dict(
                zip(list(current_prices.keys()), [self.unit_pwr]*len(current_prices))
            )
        if passes_list:
            orders = self._get_action_window(passes_list, prices=window_pred_prices)
        else:
            orders = pd.DataFrame(
                {
                    tuple([k, v, 0, TradeAction.HOLD.name])
                    for k, v in window_pred_prices.items()
                },
                columns=["hour", "value", "flow", "action"],
            )
        orders.index = window_prices.index
        orders = pd.concat([orders, window_prices["true_prices"]], axis=1)
        # set negative or null prices as BUY by default
        #orders.loc[orders.value <= 0., "action"] = TradeAction.BUY.name
        # set flow to None to let automatic flow calculation
        #orders.loc[orders.value <= 0., "flow"] = np.nan
        return orders

    def _pair_method_loop(self, current_prices, qty):
        """
        Define "while" loop for pair method (set of "passes") :
            - find min (idx, value) for a qty
            - find max (up to 2 )(idx, value) based on rest qty to sell
            - break on negative diff between sell and buy
        """

        current_diff = 0
        passes_list = self.init_passes_list()
        pos = 1
        while (
            (current_diff >= 0)
            and (len(current_prices) > 1)
            and (passes_list["iteration"] < 24)
        ):
            it = passes_list["iteration"]
            # print(f"--- PASSE : {it+1} ----")
            passe = self.init_passe()

            sell_order = 0
            buy_order = 0

            if it > 0:
                current_prices = passes_list["passes"][-1]["prices"].copy()

            #
            # BUY
            #

            min_p = self.find_min(current_prices)

            passe["min"] = {
                "qty": self.unit_pwr * 1.0,
                "value": min_p,
            }
            buy_order += min_p.value * passe["min"]["qty"]

            del current_prices[min_p.idx]

            #
            # SELL
            #

            max_p = self.find_max(current_prices)
            # we still have available max value to sell
            if passes_list["still_cpty"] > 0:
                passe["max"] = {
                    # 1h
                    "qty": np.round(
                        min(
                            self.unit_pwr * 1 * self.rho_d * self.rho_s,
                            passes_list["still_cpty"],
                        ),
                        3,
                    ),
                    "value": max_p,
                }

                qty[max_p.idx] = np.round(qty[max_p.idx] - passe["max"]["qty"], 3)

                passes_list["still_cpty"] -= passe["max"]["qty"]

                # we can sell a qty of second max value
                sell_order += max_p.value * passe["max"]["qty"]

                if qty[max_p.idx] <= 0:
                    pos = 0
                    #print("DEL")
                    del current_prices[max_p.idx]

                if len(current_prices) == 0:
                    #
                    # CHANGE HERE
                    #
                    return dict(passes=passes_list, reason="empty prices list")

                if not self.check_max_sell(passe["max"]["qty"]):
                    # print(current_prices)
                    max_p = self.find_max(current_prices, pos=pos)
                    # reset position for second maxixum
                    pos = 1

                    passe["max2"] = {
                        # 1h
                        "qty": np.round(
                            np.round(self.unit_pwr * 1.0 * self.rho_d * self.rho_s, 1)
                            - passe["max"]["qty"],
                            1,
                        ),
                        "value": max_p,
                    }
                    qty[max_p.idx] = np.round(qty[max_p.idx] - passe["max2"]["qty"], 1)
                    sell_order += max_p.value * passe["max2"]["qty"]

                    passes_list["still_cpty"] = (
                        self.unit_pwr * 1.0 - passe["max2"]["qty"]
                    )

                    if qty[max_p.idx] <= 0:
                        del current_prices[max_p.idx]

            else:
                passe["max"] = {
                    "qty": np.round(self.unit_pwr * 1.0 * self.rho_d * self.rho_s, 1),
                    "value": max_p,
                }
                passes_list["still_cpty"] = self.unit_pwr - (
                    np.round(self.unit_pwr * 1.0 * self.rho_d * self.rho_s, 1)
                )

                sell_order += max_p.value * passe["max"]["qty"]
                qty[max_p.idx] = np.round(qty[max_p.idx] - passe["max"]["qty"], 1)

                if qty[max_p.idx] <= 0:
                    del current_prices[max_p.idx]
            # --- info ---
            #print(f"""SELL : {passe["max"]["value"]} -- qty : {passe["max"]["qty"]}""")
            #print(
            #    f"""SELL : {passe["max2"]["value"]} -- qty : {passe["max2"]["qty"]}"""
            #)
            #print(f"""BUY : {passe["min"]["value"]} -- qty : {passe["min"]["qty"]}""")

            ##
            # GAIN
            ##
            passe["diff"] = np.round(sell_order - buy_order, 1)
            current_diff = passe["diff"]

            passe["prices"] = current_prices
            # print(current_prices)

            if passe["diff"] < 0:
                #print(f"""OUT : {passe["diff"]} => back passe {it}""")
                # print(f"""RESTE : {passes_list["still_cpty"]}""")
                return dict(passes=passes_list, reason="diff")
            passes_list["passes"].append(passe)

            passe["prices"]
            passes_list["iteration"] += 1

        return dict(passes=passes_list, reason="normal")

    def check_max_sell(self, qty):
        return qty >= np.round(self.unit_pwr * self.rho_d * self.rho_s, 1)

    def _get_action_window(self, passes_list, prices):
        """associate buy/sell/hold value to each hour and price"""

        it = passes_list["iteration"]
        sell_order = [
            tuple(
                [
                    _["max"]["value"].idx,
                    _["max"]["value"].value,
                    _["max"]["qty"],
                    _["max"]["value"].type_order,
                ]
            )
            for _ in passes_list["passes"]
        ]
        sell2_order = [
            tuple(
                [
                    _["max2"]["value"].idx,
                    _["max2"]["value"].value,
                    _["max2"]["qty"],
                    _["max2"]["value"].type_order,
                ]
            )
            for _ in passes_list["passes"]
            if isinstance(_["max2"]["value"], Price)
        ]
        buy_order = [
            tuple(
                [
                    _["min"]["value"].idx,
                    _["min"]["value"].value,
                    _["min"]["qty"],
                    _["min"]["value"].type_order,
                ]
            )
            for _ in passes_list["passes"]
        ]
        sell_order = sell2_order + sell_order
        orders = pd.DataFrame(
            sell_order + buy_order, columns=["hour", "value", "flow", "action"]
        )
        orders = (
            orders.groupby(["hour", "value"])
            .agg(flow=("flow", sum), action=("action", "first"))
            .reset_index()
        )
        hold_orders = pd.DataFrame(
            [
                tuple([k, v, 0, TradeAction["HOLD"].name])
                for k, v in prices.items()
                if k not in list(orders["hour"])
            ],
            columns=["hour", "value", "flow", "action"],
        )

        orders = pd.concat([orders, hold_orders]).set_index("hour").sort_index()
        # res.reindex(full_idx)
        return orders

    def search_sBb(self, passes_list):
        """return the first pass (frop the end) we sell before buy"""
        lenght = len(passes_list["passes"][::-1])

        for idx, passe in enumerate(passes_list["passes"][::-1]):
            sell_idx = (
                min(passe["max"]["value"].idx, passe["max2"]["value"].idx)
                if isinstance(passe["max2"]["value"], Price)
                else passe["max"]["value"].idx
            )
            buy_idx = passe["min"]["value"].idx
            if sell_idx < buy_idx:
                # print(f"FIND sBb FOR PASSE {lenght-idx} ")
                # idx = len(passes_list["passes"]) - idx
                return buy_idx
        return None

    def search_bBs(self, passes_list):
        """return the first pass (frop the end) we buy before sell"""

        for idx, passe in enumerate(passes_list["passes"][::-1]):
            sell_idx = (
                min(passe["max"]["value"].idx, passe["max2"]["value"].idx)
                if isinstance(passe["max2"]["value"], Price)
                else passe["max"]["value"].idx
            )
            buy_idx = passe["min"]["value"].idx
            if buy_idx < sell_idx:
                # idx = len(passes_list["passes"]) - idx
                return sell_idx
        return None

    def init_passe(self):
        return {
            "max": {
                "qty": 0,
                "value": 0,
            },
            "max2": {
                "qty": 0,
                "value": 0,
            },
            "min": {
                "qty": 0,
                "value": 0,
            },
            "diff": None,
        }

    def init_passes_list(self):
        return {
            "still_cpty": 0,
            "passes": [],
            "stock": [self.night_stock],
            "gain": [],
            "iteration": 0,
        }

    def find_max(self, prices, pos=0):
        # prevent for looking second max when we have only one price still activated
        pos=min(pos, len(prices)-1)
        max_ = sorted(prices.items(), key=lambda x: (x[1], [0]), reverse=True)[pos]
        return Price(idx=max_[0], value=max_[1], type_order=TradeAction["SELL"].name)

    def find_min(self, prices, pos=0):
        min_ = sorted(prices.items(), key=lambda x: (x[1], [0]), reverse=False)[pos]
        return Price(idx=min_[0], value=min_[1], type_order=TradeAction["BUY"].name)

    def test_loop(self, window_prices):
        current_prices = window_prices.copy()
        qty = dict(zip(np.arange(0, len(current_prices)), np.ones(len(current_prices))))
        dict_res = self._pair_method_loop(current_prices, qty)
        return dict_res
