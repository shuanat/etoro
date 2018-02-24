import json
from datetime import datetime
from typing import List, Dict

from providers.abc import BaseProvider
from providers.data_classess import Tick
from logger.logger import logger
from providers.tinkoff.data_classess import (InstrumentList)
from strategies.abc import BaseStrategy


class TinkofProvider(BaseProvider):
    def __init__(self, loop, strategy: BaseStrategy):
        super().__init__(loop)
        self.strategy = strategy
        self.default_header = {
           'content-type': 'application/json;charset=UTF-8'
        }

    async def execute(self):
        instruments = await self.get_instruments()
        max_rows = 0
        instruments_history = {}  # type: Dict[str]List
        instruments_story = {}  # type: Dict[str]InstrumentList
        for num, instrument in enumerate(instruments):
            history = await self.get_history(instrument.instrument_id)
            if len(history) > max_rows:
                max_rows = len(history)
            instruments_history[instrument.instrument_display_name] = history
            instruments_story[instrument.instrument_display_name] = instrument
        logger.debug("Count: {}, MaxRow: {}".format(len(instruments_story), max_rows))
        for row in range(max_rows):
            for display_name in instruments_history:
                tick = instruments_history[display_name][row]
                try:
                    self.strategy.tick(Tick(time=datetime.fromtimestamp(tick[0]), price=tick[1],
                                       instrument_name=display_name,
                                       lot_size=instruments_story[display_name].lot_size,
                                       instrument_id=instruments_story[display_name].instrument_id)
                                       )
                except TypeError as e:
                    logger.error(e)
        self.strategy.finish()

    async def get_instruments(self) -> List[InstrumentList]:
        return_data = []  # type: List[InstrumentList]
        url = 'https://api.tinkoff.ru/trading/stocks/list?pageSize=12&currentPage=0&start=0&end=12&sortType=ByEarnings&orderType=Desc&country=Russian'
        instruments = await self.get(url, self.default_header)
        for d in json.loads(instruments)["payload"]["values"]:
            if d["symbol"]["symbolType"] != "Stock":
                continue
            instrument = InstrumentList(instrument_id=d["symbol"]["ticker"],
                                        instrument_display_name=d["symbol"]["showName"],
                                        stock_industry_id=0,
                                        symbol_full=d["symbol"]["showName"],
                                        lot_size=d["symbol"]["lotSize"]
                                        )
            return_data.append(instrument)
        return return_data

    async def get_history(self, instrument_id: str=None) -> list:
        day_start = '2018-01-24'
        day_end = datetime.now().strftime("%Y-%m-%d")
        resolution = "D"
        url = 'https://api.tinkoff.ru/trading/symbols/historical_data?ticker={}&from={}T21%3A00%3A00.000Z&to={}T06%3A02%3A51.779Z&resolution={}'.format(
                                                                                      instrument_id, day_start, day_end, resolution)
        data = await self.get(url, self.default_header)
        return json.loads(data)["payload"]["data"]
