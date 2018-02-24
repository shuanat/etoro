import json
from datetime import datetime
from typing import Tuple, List, Dict

from providers.abc import BaseProvider
from providers.etoro import helpers
from config import login_data
from logger.logger import logger
from providers.etoro.data_classess import (InstrumentList)
from strategies.abc import BaseStrategy


class EtoroProvider(BaseProvider):

    def __init__(self, loop, strategy: BaseStrategy):
        super().__init__(loop)
        self.account_type = "Real"
        self.default_header = {
           'content-type': 'application/json;charset=UTF-8',
           'AccountType': self.account_type,
           'ApplicationIdentifier': 'ReToro',
           'ApplicationVersion': '81.0.3',
           'X-CSRF-TOKEN': '0ZXGU2PZRmJbiWpi%7CXv1tg__',
           'X-DEVICE-ID': helpers.device_id(),
           'X-STS-ClientTime': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }
        self.strategy = strategy

    async def login(self):
        domain = "https://www.etoro.com/"
        await self.get("{}/login".format(domain), self.default_header)
        url = '{}api/sts/v2/login/?client_request_id={}'.format(domain, helpers.device_id())
        headers = self.default_header
        response = await self.post(url, data=json.dumps(login_data), headers=headers)
        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError:
            logger.debug(response)
            return
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
        max_rows = 0
        instruments_history = {}  # type: Dict[str]InstrumentList
        for num, instrument in enumerate(instruments):
            history = await self.get_history(instrument.instrument_id)
            if len(history) > max_rows:
                max_rows = len(history)
                instruments_history[instrument.instrument_display_name] = instrument
        
        for row in range(max_rows):
            for display_name in instruments_history:
                raw_tick = instruments_history[display_name][row]
                self.strategy.tick(Tick())


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




