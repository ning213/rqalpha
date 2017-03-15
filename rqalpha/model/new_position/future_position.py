# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .base_position import BasePosition
from ...execution_context import ExecutionContext
from ...environment import Environment
from ...const import SIDE, POSITION_EFFECT


class FuturePostion(BasePosition):
    def __init__(self, order_book_id):
        super(FuturePostion, self).__init__(order_book_id)

        self._buy_old_holding_list = []
        self._sell_old_holding_list = []
        self._buy_today_holding_list = []
        self._sell_today_holding_list = []

        self._buy_transaction_cost = 0.
        self._sell_transaction_cost = 0.
        self._buy_realized_pnl = 0.
        self._sell_realized_pnl = 0.

        self._buy_avg_open_price = 0.
        self._sell_avg_open_price = 0.

    @property
    def margin_rate(self):
        return ExecutionContext.get_future_margin(self.order_book_id)

    @property
    def margin_multiplier(self):
        return Environment.get_instance().config.base.margin_multiplier

    # -- PNL 相关
    @property
    def contract_multiplier(self):
        return ExecutionContext.get_instrument(self.order_book_id).contract_multiplier

    @property
    def open_orders(self):
        return ExecutionContext.get_open_orders(self.order_book_id)

    @property
    def buy_holding_pnl(self):
        """
        [float] 买方向当日持仓盈亏
        """
        return (self._last_price - self._buy_avg_open_price) * self.buy_quantity * self.contract_multiplier

    @property
    def sell_holding_pnl(self):
        """
        [float] 卖方向当日持仓盈亏
        """
        return (self._sell_avg_open_price - self._last_price) * self.sell_quantity * self.contract_multiplier

    @property
    def buy_realized_pnl(self):
        """
        [float] 买方向平仓盈亏
        """
        return self._buy_realized_pnl

    @property
    def sell_realized_pnl(self):
        """
        [float] 卖方向平仓盈亏
        """
        return self._sell_realized_pnl

    @property
    def holding_pnl(self):
        """
        [float] 当日持仓盈亏
        """
        return self.buy_holding_pnl + self.sell_holding_pnl

    @property
    def realized_pnl(self):
        """
        [float] 当日平仓盈亏
        """
        return self.buy_realized_pnl + self.sell_realized_pnl

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        return self.holding_pnl + self.realized_pnl

    @property
    def buy_pnl(self):
        """
        [float] 买方向累计盈亏
        """
        return (self._last_price - self._buy_avg_open_price) * self.buy_quantity * self.contract_multiplier

    @property
    def sell_pnl(self):
        """
        [float] 卖方向累计盈亏
        """
        return (self._sell_avg_open_price - self._last_price) * self.sell_quantity * self.contract_multiplier

    @property
    def pnl(self):
        """
        [float] 累计盈亏
        """
        return self.buy_pnl + self.sell_pnl

    # -- Quantity 相关
    @property
    def buy_open_order_quantity(self):
        """
        [int] 买方向挂单量
        """
        return sum(order.unfilled_quantity for order in self.open_orders if
                   order.side == SIDE.BUY and order.position_effect == POSITION_EFFECT.OPEN)

    @property
    def sell_open_order_quantity(self):
        """
        [int] 卖方向挂单量
        """
        return sum(order.unfilled_quantity for order in self.open_orders if
                   order.side == SIDE.SELL and order.position_effect == POSITION_EFFECT.OPEN)

    @property
    def buy_close_order_quantity(self):
        """
        [int] 买方向挂单量
        """
        return sum(order.unfilled_quantity for order in self.open_orders if order.side == SIDE.BUY and
                   order.position_effect in [POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY])

    @property
    def sell_close_order_quantity(self):
        """
        [int] 卖方向挂单量
        """
        return sum(order.unfilled_quantity for order in self.open_orders if order.side == SIDE.SELL and
                   order.position_effect in [POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY])

    @property
    def buy_old_quantity(self):
        """
        [int] 买方向昨仓
        """
        return sum(amount for price, amount in self._buy_old_holding_list)

    @property
    def sell_old_quantity(self):
        """
        [int] 卖方向昨仓
        """
        return sum(amount for price, amount in self._sell_old_holding_list)

    @property
    def buy_today_quantity(self):
        """
        [int] 买方向今仓
        """
        return sum(amount for price, amount in self._buy_today_holding_list)

    @property
    def sell_today_quantity(self):
        """
        [int] 卖方向今仓
        """
        return sum(amount for price, amount in self._sell_today_holding_list)

    @property
    def buy_quantity(self):
        """
        [int] 买方向持仓
        """
        return self.buy_old_quantity + self.buy_today_quantity

    @property
    def sell_quantity(self):
        """
        [int] 卖方向持仓
        """
        return self.sell_old_quantity + self.sell_today_quantity

    @property
    def closable_buy_quantity(self):
        """
        [float] 可平买方向持仓
        """
        return self.buy_quantity - self.sell_close_order_quantity

    @property
    def closable_sell_quantity(self):
        """
        [float] 可平卖方向持仓
        """
        return self.sell_quantity - self.buy_close_order_quantity

    @property
    def _quantity(self):
        # TODO
        raise NotImplementedError

    # -- Margin 相关
    @property
    def buy_margin(self):
        """
        [float] 买方向持仓保证金
        """
        return self._buy_holding_cost * self.margin_rate * self.margin_multiplier

    @property
    def sell_margin(self):
        """
        [float] 卖方向持仓保证金
        """
        return self._sell_holding_cost * self.margin_rate * self.margin_multiplier

    @property
    def margin(self):
        """
        [float] 保证金
        """
        # TODO 需要添加单向大边相关的处理逻辑
        return self.buy_margin + self.sell_margin

    @property
    def buy_avg_holding_price(self):
        """
        [float] 买方向持仓均价
        """
        return 0 if self.buy_quantity == 0 else self._buy_holding_cost / self.buy_quantity / self.contract_multiplier

    @property
    def sell_avg_holding_price(self):
        """
        【float】卖方向持仓均价
        """
        return 0 if self.sell_quantity == 0 else self._sell_holding_cost / self.sell_quantity / self.contract_multiplier

    @property
    def _buy_holding_cost(self):
        return sum(p * a * self.contract_multiplier for p, a in self.buy_holding_list)

    @property
    def _sell_holding_cost(self):
        return sum(p * a * self.contract_multiplier for p, a in self.sell_holding_list)

    @property
    def buy_holding_list(self):
        return self._buy_old_holding_list + self._buy_today_holding_list

    @property
    def sell_holding_list(self):
        return self._sell_old_holding_list + self._sell_today_holding_list

    @property
    def buy_avg_open_price(self):
        return self._buy_avg_open_price

    @property
    def sell_avg_open_price(self):
        return self._sell_avg_open_price

    @property
    def buy_transaction_cost(self):
        return self._buy_transaction_cost

    @property
    def sell_transaction_cost(self):
        return self._sell_transaction_cost

    @property
    def transaction_cost(self):
        return self._buy_transaction_cost + self._sell_transaction_cost

    # -- Function

    def _cal_close_today_amount(self, trade_amount, trade_side):
        if trade_side == SIDE.SELL:
            close_today_amount = trade_amount - self.buy_old_quantity
        else:
            close_today_amount = trade_amount - self.sell_old_quantity
        return max(close_today_amount, 0)

    def apply_settlement(self):
        data_proxy = Environment.get_instance().data_proxy
        trading_date = ExecutionContext.get_current_trading_dt().date()
        settle_price = data_proxy.get_settle_price(self.order_book_id, trading_date)
        self._buy_old_holding_list = [(settle_price, self.buy_quantity)]
        self._sell_old_holding_list = [(settle_price, self.sell_quantity)]
        self._buy_today_holding_list = []
        self._sell_today_holding_list = []

        self._buy_transaction_cost = 0.
        self._sell_transaction_cost = 0.
        self._buy_realized_pnl = 0.
        self._sell_realized_pnl = 0.

    def apply_trade(self, trade):
        order = trade.order
        trade_quantity = trade.last_quantity
        if order.side == SIDE.BUY:
            if order.position_effect == POSITION_EFFECT.OPEN:
                self._buy_avg_open_price = (self._buy_avg_open_price * self.buy_quantity +
                                            trade_quantity * trade.last_price) / (self.buy_quantity + trade_quantity)
                self._buy_transaction_cost += trade.commission
                self._buy_today_holding_list.insert(0, (trade.last_price, trade_quantity))
            else:
                self._sell_transaction_cost += trade.commission
                delta_realized_pnl = self._close_holding(trade)
                self._sell_realized_pnl += delta_realized_pnl
        else:
            if order.position_effect == POSITION_EFFECT.OPEN:
                self._sell_avg_open_price = (self._sell_avg_open_price * self.sell_quantity +
                                             trade_quantity * trade.last_price) / (self.sell_quantity + trade_quantity)
                self._sell_transaction_cost += trade.commission
                self._sell_today_holding_list.insert(0, (trade.last_price, trade_quantity))
            else:
                self._buy_transaction_cost += trade.commission
                delta_realized_pnl = self._close_holding(trade)
                self._buy_realized_pnl += delta_realized_pnl

    def _close_holding(self, trade):
        order = trade.order
        order_book_id = order.order_book_id
        left_quantity = trade.last_quantity
        delta_daily_realized_pnl = 0
        if order.side == SIDE.BUY:
            # 先平昨仓
            if len(self._sell_old_holding_list) != 0:
                old_price, old_quantity = self._sell_old_holding_list.pop()

                if old_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    self._sell_old_holding_list = [(old_price, old_quantity - left_quantity)]
                else:
                    consumed_quantity = left_quantity
                left_quantity -= consumed_quantity
                delta_daily_realized_pnl += self._cal_realized_pnl(trade, old_price, consumed_quantity)
            # 再平进仓
            while True:
                if left_quantity <= 0:
                    break
                oldest_price, oldest_quantity = self._sell_today_holding_list.pop()
                if oldest_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    self._sell_today_holding_list.append((oldest_price, oldest_quantity - left_quantity))
                else:
                    consumed_quantity = oldest_quantity
                left_quantity -= consumed_quantity
                delta_daily_realized_pnl += self._cal_realized_pnl(trade, oldest_price, consumed_quantity)
        else:
            # 先平昨仓
            while True:
                if left_quantity == 0:
                    break
                if len(self._buy_old_holding_list) == 0:
                    break
                oldest_price, oldest_quantity = self._buy_old_holding_list.pop()
                if oldest_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    self._buy_old_holding_list.append((oldest_price, oldest_quantity - left_quantity))
                else:
                    consumed_quantity = oldest_quantity
                left_quantity -= consumed_quantity
                delta_daily_realized_pnl += self._cal_daily_realized_pnl(trade, settle_price, consumed_quantity)
            # 再平今仓
            while True:
                if left_quantity <= 0:
                    break
                oldest_price, oldest_quantity = self._buy_today_holding_list.pop()
                if oldest_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    self._buy_today_holding_list.append((oldest_price, oldest_quantity - left_quantity))
                    left_quantity = 0
                else:
                    consumed_quantity = oldest_quantity
                left_quantity -= consumed_quantity
                delta_daily_realized_pnl += self._cal_daily_realized_pnl(trade, oldest_price, consumed_quantity)
        return delta_daily_realized_pnl