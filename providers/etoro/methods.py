import json
from datetime import datetime
from typing import Tuple, List

import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint
# from matplotlib import pyplot
import numpy
import statsmodels.formula.api as sm

from providers.abc import BaseProvider
from providers.etoro import helpers
from config import login_data
from logger.logger import logger
from providers.etoro.data_classess import Instrument, InstrumentHistory, SpreadInstrument


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
        for num, instrument in enumerate(json.loads(instruments)["InstrumentDisplayDatas"]):
            history = await self.get_history(instrument["InstrumentID"])
            is_adfuller, series = self.check_adfuller(json.loads(history))
            if is_adfuller:
                rows.append(Instrument(id=instrument["InstrumentID"], name=instrument["InstrumentDisplayName"],
                                       series=series))
            if num > 2:
                break
        rows = self.check_coin(rows)
        print(rows)

    async def get_instruments(self) -> dict:
        url = 'https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments'
        return await self.get(url, self.default_header)

    async def get_history(self, instrument_id: int=None, count=1000):
        url = 'https://candle.etoro.com/candles/desc.json/ThirtyMinutes/{}/{}'.format(count, instrument_id)
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

        for key_h1, h1 in enumerate(history):
            for key_h2, h2 in enumerate(history):
                if key_h1 == key_h2:
                    continue
                data = coint(h1.series, h2.series)  # type: List
                if data[1] > cutoff:
                    l_history.append(InstrumentHistory(series=[h1.series, h2.series], id=[h1.id, h2.id],
                                                       name=[h1.name, h2.name]))

        for row in l_history:
            h1_coord = []
            h2_coord = []
            y1 = []
            y2 = []
            x = []
            for key, r in enumerate(row.series[0]):
                h1_coord.append([key, row.series[0][key]])
                h2_coord.append([key, row.series[1][key]])
                y1.append(row.series[0][key])
                y2.append(row.series[1][key])
                x.append(numpy.divide(key, 2))
            df = pd.DataFrame()
            df["X"] = x
            df["Y1"] = y1
            df["Y2"] = y2
            results = sm.ols(formula='X ~ Y1 + Y2', data=df).fit()
            y = [v for v in results.resid]
            # pyplot.plot(x, y1)
            # pyplot.plot(x, y2)
            # pyplot.plot(x, y)
            # pyplot.show()
            return_data.append(SpreadInstrument(spread=y[-1], name=row.name, id=row.id))
        return return_data
