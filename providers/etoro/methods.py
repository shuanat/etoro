import json
from datetime import datetime
from typing import Tuple, List, Dict

import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint
from matplotlib import pyplot
import numpy
import statsmodels.formula.api as sm

from providers.abc import BaseProvider
from providers.etoro import helpers
from config import login_data
from logger.logger import logger
from providers.etoro.data_classess import (Instrument, InstrumentHistory,
                                           SpreadInstrument, InstrumentList)


class EtoroProvider(BaseProvider):

    def __init__(self, loop):
        super().__init__(loop)
        self.account_type = "Real"
        self.default_header = {
           'content-type': 'application/json;charset=UTF-8',
           'AccountType': self.account_type,
           'ApplicationIdentifier': 'ReToro',
           'ApplicationVersion': '81.0.3',
           'X-CSRF-TOKEN': 'Nss4qvZi3zrBlSyhW399wA%5f%5f',
           'X-DEVICE-ID': helpers.device_id(),
           'X-STS-ClientTime': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }

    async def login(self):
        domain = "https://www.etoro.com/"
        await self.get("{}/login".format(domain), self.default_header)
        url = '{}api/sts/v2/login/?client_request_id={}'.format(domain, helpers.device_id())
        headers = self.default_header
        response = await self.post(url, data=json.dumps(login_data), headers=headers)
        response_dict = json.loads(response)
        logger.debug(response_dict)
        access_token = response_dict.get("accessToken", None)
        self.default_header['Authorization'] = access_token

    async def get_login_info(self) -> dict:
        params = {'client_request_id': helpers.device_id(),
                  'conditionIncludeDisplayableInstruments': 'false',
                  'conditionIncludeMarkets': 'false',
                  'conditionIncludeMetadata': 'false',
                  }
        data = await self.get('https://www.etoro.com/api/logininfo/v1.1/logindata', params)
        return data

    async def execute(self):
        await self.login()
        instruments = await self.get_instruments()
        rows = []
        for num, instrument in enumerate(instruments):
            history = await self.get_history(instrument.instrument_id)
            is_adfuller, series = self.check_adfuller(json.loads(history))
            if is_adfuller:
                rows.append(Instrument(id=instrument.instrument_id,
                                       name=instrument.instrument_display_name, series=series))
            if num >= 5:
                break
        rows = self.check_coin(rows)
        for r in rows:
            print(r.name[0], r.name[1], r.spread)

    async def get_instruments(self) -> List[InstrumentList]:
        return_data = []  # type: List[InstrumentList]
        url = 'https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments'
        instruments = await self.get(url, self.default_header)
        for d in json.loads(instruments)["InstrumentDisplayDatas"]:
            if d.get("StocksIndustryID", None) is None:
                continue
            return_data.append(InstrumentList(instrument_id=d["InstrumentID"],
                                              instrument_display_name=d["InstrumentDisplayName"],
                                              stock_industry_id=d["StocksIndustryID"],
                                              symbol_full=d["SymbolFull"]))
        return return_data

    async def get_history(self, instrument_id: int=None, count=1000):
        url = 'https://candle.etoro.com/candles/desc.json/ThirtyMinutes/{}/{}'.format(count,
                                                                                      instrument_id)
        # url = 'https://candle.etoro.com/candles/desc.json/FiveMinutes/1000/1'
        data = await self.get(url, self.default_header)
        return data

    @staticmethod
    def check_adfuller(history: dict, cutoff: float=0.05) -> Tuple[bool, pd.Series]:
        time_series = {}
        for row in history["Candles"]:
            for candle in row["Candles"]:
                time_series[candle["FromDate"]] = candle["Close"]
        s = pd.Series(time_series)
        result = adfuller(s)  # type: List
        if result[1] > cutoff:
            logger.debug("Bingo: {}, {}, {}".format(result[0], result[4]["5%"], result[1]))
            # pyplot.plot(s)
            # pyplot.show()
            return True, s
        return False, s

    @staticmethod
    def check_coin(history: List[Instrument], cutoff: float=0.05) -> List[SpreadInstrument]:
        return_data = []  # type: List[SpreadInstrument]
        l_history = []  # type: List[InstrumentHistory]
        is_checked = {}  # type: Dict[str]bool
        for key_h1, h1 in enumerate(history):
            for key_h2, h2 in enumerate(history):
                # проверка, чтобы два раза не дублировались данные
                direct_name = '{}{}'.format(h2.name, h1.name)
                revert_name = '{}{}'.format(h1.name, h2.name)
                if is_checked.get(direct_name, None) is not None or is_checked.get(revert_name, None) is not None:
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
            #pyplot.plot(x, y1)
            #pyplot.plot(x, y2)
            # pyplot.plot(x, y)
            # pyplot.show()
            return_data.append(SpreadInstrument(spread=y[-1], name=row.name, id=row.id))
        return return_data
