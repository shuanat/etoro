from providers.data_classess import Tick

class BaseStrategy:

    def __init__(self, loop):
        self.loop = loop
        self.orders = []
        self.balance = 100000

    def buy(self, tick: Tick, count: int):
        self.balance -= tick.price*count
        self.orders.append({"count": count, "tick": tick})

    def sell(self, tick: Tick, count: int):
        for key, order in enumerate(self.orders):
            if order["tick"].instrument_id == tick.instrument_id:
                if order["count"] == count:
                    self.balance += tick.price * count
                    self.orders.pop(key)
                    break

    def tick(self, tick: Tick):
        raise NotImplemented

    def finish(self):
        raise NotImplemented
