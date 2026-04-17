from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import statistics
import collections

class Trader:
    def __init__(self):
        # Keep track of recent mid-prices to handle thin books
        self.market_history = collections.defaultdict(lambda: collections.deque(maxlen=4))
        self.position_limit = {"ASH_COATED_OSMIUM": 60, "INTARIAN_PEPPER_ROOT": 80}
        self.pepper_init_value = None

    def run(self, state: TradingState):
        if self.pepper_init_value == None:
            best_ask = sorted(state.order_depths["INTARIAN_PEPPER_ROOT"].sell_orders.items())[0][0]
            best_bid = sorted(state.order_depths["INTARIAN_PEPPER_ROOT"].buy_orders.items(), reverse=True)[0][0]
            self.pepper_init_value = round(best_ask + best_bid / 2)

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

    def trade_pepper(self, state: TradingState, order_depth: OrderDepth) -> List[Order]:
        orders: List[Order] = []
        product = "INTARIAN_PEPPER_ROOT"

        sell_orders = sorted(order_depth.sell_orders.items())              # asks: (price, negative qty)
        buy_orders = sorted(order_depth.buy_orders.items(), reverse=True)  # bids: (price, positive qty)

        if not sell_orders and not buy_orders:
            return orders

        cur_position = state.position.get(product, 0)
        limit = self.position_limit[product]

        best_ask = sell_orders[0][0] if sell_orders else None
        best_bid = buy_orders[0][0] if buy_orders else None

        # Slow upward anchor
        fair_value = self.pepper_init_value + state.timestamp / 1000.0

        # 1) Early accumulation: get to 80 quickly, but reduce initial spread cost
        early_cutoff = 3000

        if state.timestamp < early_cutoff and cur_position < limit:
            remaining = limit - cur_position

            # Take only part of the visible ask aggressively
            aggressive_take = max(1, remaining // 2)

            for price, amount in sell_orders:
                if aggressive_take <= 0 or remaining <= 0:
                    break

                available = -amount
                qty = min(aggressive_take, available, remaining)
                if qty > 0:
                    orders.append(Order(product, price, qty))
                    aggressive_take -= qty
                    remaining -= qty

            # Rest: strong bid near top of book
            if remaining > 0 and best_bid is not None:
                bid_px = best_bid + 1
                if best_ask is not None and bid_px >= best_ask:
                    bid_px = best_ask - 1
                orders.append(Order(product, bid_px, remaining))

            return orders

        # 2) After build: stay long, only trade lightly around full inventory
        target_hold = 80
        sell_floor = 75

        buy_room = max(0, target_hold - cur_position)
        sell_room = max(0, cur_position - sell_floor)

        # Rebuy dips back toward 80
        for price, amount in sell_orders:
            if buy_room <= 0:
                break

            available = -amount
            if price <= fair_value - 1:
                qty = min(buy_room, available)
                if qty > 0:
                    orders.append(Order(product, price, qty))
                    buy_room -= qty

        # Sell only if clearly expensive
        for price, amount in buy_orders:
            if sell_room <= 0:
                break

            available = amount
            if price >= fair_value + 5:
                qty = min(sell_room, available)
                if qty > 0:
                    orders.append(Order(product, price, -qty))
                    sell_room -= qty

        # Small passive inventory management
        if buy_room > 0 and best_bid is not None:
            bid_px = min(int(fair_value - 1), best_bid + 1)
            if best_ask is not None and bid_px >= best_ask:
                bid_px = best_ask - 1
            orders.append(Order(product, bid_px, min(5, buy_room)))

        if sell_room > 0 and best_ask is not None:
            ask_px = max(int(fair_value + 5), best_ask - 1)
            if best_bid is not None and ask_px <= best_bid:
                ask_px = best_bid + 1
            orders.append(Order(product, ask_px, -min(5, sell_room)))

        return orders 

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
        skew = round(current_pos / limit * 0.5) 
        
        bid_price = max(round(fair_value) - 6 - skew, round(fair_value) - 10)
        ask_price = min(round(fair_value) + 6 - skew, round(fair_value) + 10)

        orders.append(Order(product, bid_price, limit - current_pos))
        orders.append(Order(product, ask_price, -limit - current_pos))

        return orders, fair_value