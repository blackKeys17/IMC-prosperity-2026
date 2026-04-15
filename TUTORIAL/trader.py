from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

class Trader:
    def run(self, state: TradingState):
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders = []
            
            # Separate strategies for each product
            wall_mid = ""
            if product == "ASH_COATED_OSMIUM":
                orders, wall_mid = self.trade_ash(state, order_depth)
            elif product == "INTARIAN_PEPPER_ROOT":
                orders = self.trade_pepper(state, order_depth)

            result[product] = orders
        
        conversions = 0
        if wall_mid == "":
            trader_data = state.traderData
        else:
            trader_data = str(wall_mid)

        return result, conversions, trader_data
    
    def trade_ash(self, state: TradingState, order_depth):
        orders: List[Order] = []
        product = "ASH_COATED_OSMIUM"
        threshold = 25
        
        # Estimate fair value
        enough_orders = True

        sell_orders = sorted(list(order_depth.sell_orders.items()), key=lambda k: k[0])
        cumulative_orders = 0
        wall_bid = 0
        
        for price, amount in sell_orders:
            wall_bid = price
            cumulative_orders += abs(amount)
            if cumulative_orders >= threshold:
                break
        if cumulative_orders < threshold:
            enough_orders = False
        
        buy_orders = sorted(list(order_depth.buy_orders.items()), key=lambda k: k[0], reverse=True)
        cumulative_orders = 0
        wall_ask = 0
        
        for price, amount in buy_orders:
            wall_ask = price
            cumulative_orders += amount
            if cumulative_orders >= threshold:
                break
        if cumulative_orders < threshold:
            enough_orders = False

        if enough_orders:
            wall_mid = (wall_bid + wall_ask) / 2
        else:
            if not state.traderData:
                return [], ""
            else:
                wall_mid = float(state.traderData)
        
        for price, amount in sell_orders:
            if price < wall_mid:
                orders.append(Order(product, price, -amount))
        
        for price, amount in buy_orders:
            if price > wall_mid:
                orders.append(Order(product, price, -amount))
        
        orders.append(Order(product, int(wall_mid)-2, 15))
        orders.append(Order(product, int(wall_mid)+2, -15))

        return orders, wall_mid

    def trade_pepper(self, state: TradingState, order_depth):
        orders: List[Order] = []
        product = "INTARIAN_PEPPER_ROOT"

        fair_value = 12000 + state.timestamp // 100

        cur_position = state.position.get(product, 0)
        if cur_position != None:
            if cur_position < 70:
                orders.append(Order(product, fair_value-2, 80-cur_position))
            else:
                orders.append(Order(product, fair_value+2, -20))
        
        return []