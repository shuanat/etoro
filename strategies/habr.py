from typing import Tuple, List

import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint
from matplotlib import pyplot
import numpy
import statsmodels.formula.api as sm

from logger.logger import logger
from strategies.abc import BaseStrategy
from providers.data_classess import (Instrument, InstrumentHistory,
                                           SpreadInstrument, Tick)


class HabrStrategy(BaseStrategy):
    COUNT_CHECK_ADFULLER = 20
    MAX_ORDERS = 10

    def __init__(self, loop):
        super().__init__(loop)
        self.instruments = {}  # type: Dict[string]List[Tick]
        self.instrument_series = {}
        self.last_price = {}
        self.my_orders = {}

    @staticmethod
    def check_adfuller(history: List[Tick], cutoff: float = 0.05) -> Tuple[bool, pd.Series]:
        time_series = {}
        for row in history:
            time_series[row.time] = row.price
        s = pd.Series(time_series)
        result = adfuller(s)  # type: List
        if result[1] > cutoff:
            # pyplot.plot(s)
            # pyplot.show()
            return True, s
        return False, s

    @staticmethod
    def check_coin(history: List[Instrument], cutoff: float = 0.05) -> List[SpreadInstrument]:
        return_data = []  # type: List[SpreadInstrument]
        l_history = []  # type: List[InstrumentHistory]
        is_checked = {}  # type: Dict[str]bool
        for key_h1, h1 in enumerate(history):
            for key_h2, h2 in enumerate(history):
                # проверка, чтобы два раза не дублировались данные
                direct_name = '{}{}'.format(h2.name, h1.name)
                revert_name = '{}{}'.format(h1.name, h2.name)
                if is_checked.get(direct_name, None) is not None or is_checked.get(revert_name,
                                                                                   None) is not None:
                    continue
                is_checked[direct_name] = True
                is_checked[revert_name] = True

                if key_h1 == key_h2:
                    continue
                data = coint(h1.series, h2.series)  # type: List
                if data[1] > cutoff:
                    l_history.append(InstrumentHistory(series=[h1.series, h2.series],
                                                       id=[h1.id, h2.id], name=[h1.name, h2.name]))

        for row in l_history:
            y1 = []
            y2 = []
            x = []
            for key, _ in enumerate(row.series[0]):
                y1.append(row.series[0][key])
                y2.append(row.series[1][key])
                x.append(numpy.divide(key, 2))
            df = pd.DataFrame()
            df["X"] = x
            df["Y1"] = y1
            df["Y2"] = y2
            results = sm.ols(formula='Y1 ~ Y2', data=df).fit()
            y = [v for v in results.resid]
            # pyplot.plot(x, y1)
            # pyplot.plot(x, y2)
            # pyplot.plot(x, y)
            # pyplot.show()
            return_data.append(SpreadInstrument(spread=y[-1], name=row.name, id=row.id))
        return return_data

    def tick(self, tick: Tick):
        self.last_price[tick.instrument_id] = tick
        rows = []  # type: List[Instrument]
        if self.instruments.get(tick.instrument_id) is None:
            self.instruments[tick.instrument_id] = [tick]
        self.instruments[tick.instrument_id].append(tick)
        if len(self.instruments[tick.instrument_id]) > HabrStrategy.COUNT_CHECK_ADFULLER:
            logger.debug("Check Adfuller: {}, Count: {}".format(tick.instrument_name,
                                                                len(self.instruments[tick.instrument_id])))
            is_adfuller, series = self.check_adfuller(self.instruments[tick.instrument_id])
            if is_adfuller:
                if self.instrument_series.get(tick.instrument_id) is None:
                    self.instrument_series[tick.instrument_id] = series

                if len(self.instrument_series) < 2:
                    return

                for instrument_name in self.instrument_series:
                    rows.append(Instrument(id=instrument_name, name=instrument_name, series=series))

            rows = self.check_coin(rows)
            for r in rows:
                dict_key = "{}{}".format(r.name[0], r.name[1])
                if r.spread > 0 and self.my_orders.get(dict_key) is None:
                    self.buy(tick, 1)
                if r.spread < 0 and self.my_orders.get(dict_key) is not None:
                    self.sell(tick, 1)

    def buy(self, tick: Tick, count: int):
        if len(self.orders) > HabrStrategy.MAX_ORDERS:
            return
        logger.info("buy")
        super().buy(tick, count)

    def sell(self, tick: Tick, count: int):
        logger.info("sell")
        super().sell(tick, count)

    def finish(self):
        for order in self.orders:
            self.sell(self.last_price[order["tick"].instrument_id], 1)
        print(self.balance)
