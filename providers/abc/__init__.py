from abc import ABC
import asyncio

import aiohttp

from logger import logger
from providers.etoro import helpers


class BaseProvider(ABC):

    def __init__(self, loop):
        self.session = aiohttp.ClientSession(loop=loop)
        self.timeout = 10
        self.loop = loop
        self.cookies = {
            "TMIS1": "9a74f2a102375b68ad54cc9c5bdfcf530324a4fb2fe9a337d0b22132582947cf6e439acff3154971baf83c9b2be3f5ce89c06f2ea719ae74473d6c3fb5a78894b9fc1cb01cabc90bd63e21d945dadebb0c8b372984534a6473c66cf77c3269755f6dadd2a270d38c2443c31975"
        }

    async def login(self):
        """Вход в систему"""
        raise NotImplemented

    async def get(self, url: str, headers: dict, params: dict=None) -> dict:
        """Запрос - Метод GET"""
        try:
            with aiohttp.Timeout(self.timeout):
                async with aiohttp.ClientSession(loop=self.loop, cookies=self.cookies) as session:
                    async with session.get(url, params=params, headers=headers) as response:
                        answer = await response.text()
            return answer
        except Exception as e:
            logger.error(e)
            return {}

    async def post(self, url: str, data: dict, headers: dict) -> dict:
        """Запрос - Метод POST"""
        try:
            with aiohttp.Timeout(self.timeout):
                async with aiohttp.ClientSession(loop=self.loop, cookies=self.cookies) as session:
                    async with session.post(url, data=data, headers=headers) as response:
                        answer = await response.text()
                        self.cookies = helpers.cookies_parse(response.cookies)
            return answer
        except Exception as e:
            logger.error(e)
            return {}

    async def execute(self):
        raise NotImplemented
