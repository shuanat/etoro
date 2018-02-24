from providers.data_classess import Tick
from logger.logger import logger


class BaseStrategy:

    def __init__(self, loop):
        self.loop = loop
        self.orders = []
        self.balance = 100000

    def buy(self, tick: Tick, count: int):
        if tick.price*count > self.balance:
            return False
        self.balance -= tick.price*count
        self.orders.append({"count": count, "tick": tick})
        logger.info("Buy: {}. Balance: {}".format(tick, self.balance))
        return True

    def sell(self, tick: Tick, count: int):
        for key, order in enumerate(self.orders):
            if order["tick"].instrument_id == tick.instrument_id:
                if order["count"] == count:
                    self.balance += tick.price * count
                    self.orders.pop(key)
                    logger.info("Sell: {}. Balance: {}".format(tick, self.balance))
                    return True

    def tick(self, tick: Tick):
        raise NotImplemented

    def finish(self):
        raise NotImplemented
