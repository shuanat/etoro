from providers.data_classess import Tick
from logger.logger import logger


class BaseStrategy:

    def __init__(self, loop):
        self.loop = loop
        self.orders = []
        self.balance = 100000
        self.fee = 100

    def buy(self, tick: Tick, count: int):
        if tick.price*count > (self.balance - self.fee):
            return False
        self.balance -= self.fee
        self.balance -= tick.price*count
        self.orders.append({"count": count, "tick": tick})
        logger.info("Buy: {}. Balance: {}. Count orders: {}".format(tick, self.balance, len(self.orders)))
        return True

    def sell(self, tick: Tick):
        for key, order in enumerate(self.orders):
            if order["tick"].instrument_id == tick.instrument_id:
                self.balance += tick.price * order["count"]
                self.balance -= self.fee
                self.orders.pop(key)
                logger.info("Sell: {}. Balance: {} Count orders: {}".format(tick, self.balance, len(self.orders)))
                return True

    def tick(self, tick: Tick):
        raise NotImplemented

    def finish(self):
        raise NotImplemented
