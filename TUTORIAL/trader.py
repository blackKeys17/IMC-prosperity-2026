from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import statistics
import collections

class Trader:
    def __init__(self):
        # Keep track of recent mid-prices to handle thin books
        self.market_history = collections.defaultdict(lambda: collections.deque(maxlen=4))
        self.position_limit = {"ASH_COATED_OSMIUM": 60, "INTARIAN_PEPPER_ROOT": 80}

    def run(self, state: TradingState):
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders = []

            if product == "ASH_COATED_OSMIUM":
                orders, fair_value = self.trade_ash(state, order_depth)
            elif product == "INTARIAN_PEPPER_ROOT":
                orders = self.trade_pepper(state, order_depth)

            result[product] = orders

        # Use traderData to persist the last known fair value if needed
        trader_data = ""
        if "ASH_COATED_OSMIUM" in self.market_history and self.market_history["ASH_COATED_OSMIUM"]:
            trader_data = str(self.market_history["ASH_COATED_OSMIUM"][-1])

        return result, 0, trader_data 
    
    def to_list(self, state):
        return [float(i) for i in state.traderData.split(" ")]

    # To send to next state
    def to_str(self, wall_mids):
        return " ".join([str(i) for i in wall_mids])

    def trade_pepper(self, state: TradingState, order_depth):
        orders: List[Order] = []
        product = "INTARIAN_PEPPER_ROOT"

        fair_value = 12000 + state.timestamp // 100

        cur_position = state.position.get(product, 0)
        if cur_position != None:
            if cur_position < 80:
                orders.append(Order(product, fair_value-2, 80-cur_position))
            else:
                orders.append(Order(product, fair_value+2, -20))
        
        return []

    def trade_ash(self, state: TradingState, order_depth):
        product = "ASH_COATED_OSMIUM"
        orders: List[Order] = []
        threshold = 30

        # 1. Determine Fair Value from 'Walls'
        sell_orders = sorted(order_depth.sell_orders.items())
        buy_orders = sorted(order_depth.buy_orders.items(), reverse=True)

        wall_bid, wall_ask = None, None
        vol = 0
        for p, a in sell_orders:
            vol += abs(a)
            if vol >= threshold: wall_bid = p; break

        vol = 0
        for p, a in buy_orders:
            vol += a
            if vol >= threshold: wall_ask = p; break

        if wall_bid and wall_ask:
            fair_value = (wall_bid + wall_ask) / 2
            self.market_history[product].append(fair_value)
        elif self.market_history[product]:
            fair_value = sum(self.market_history[product]) / len(self.market_history[product])
        else:
            return [], 0

        # 2. Market Taking (Aggressive)
        for price, amount in sell_orders:
            if price < fair_value - 1:
                orders.append(Order(product, price, -amount))

        for price, amount in buy_orders:
            if price > fair_value + 1:
                orders.append(Order(product, price, -amount))

        # 3. Market Making (Passive) with Inventory Skew
        current_pos = state.position.get(product, 0)
        limit = self.position_limit[product]

        # Inventory skew: adjust prices based on how far we are from zero position
        # If pos is positive (long), we want to sell easier (lower ask) and buy harder (lower bid)
        skew = int(current_pos / limit * 0.5) 
        
        bid_price = int(fair_value) - 6 - skew
        ask_price = int(fair_value) + 6 - skew

        orders.append(Order(product, bid_price, limit - current_pos))
        orders.append(Order(product, ask_price, -limit - current_pos))

        return orders, fair_value