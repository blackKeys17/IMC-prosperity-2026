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
            if product == "ASH_COATED_OSMIUM":
                orders = self.trade_ash(state, order_depth)
            elif product == "INTARIAN_PEPPER_ROOT":
                orders = self.trade_pepper(state, order_depth)

            result[product] = orders
        
        return result, 0, "SAMPLE"
    
    def trade_ash(self, state: TradingState, order_depth):
        orders: List[Order] = []
        product = "ASH_COATED_OSMIUM"
        
        best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
        orders.append(Order(product, best_ask, -best_ask_amount))
            
        best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
        orders.append(Order(product, best_bid, best_bid_amount))

        return []

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
        
        return orders