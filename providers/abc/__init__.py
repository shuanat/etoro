from abc import ABC
import asyncio

import aiohttp

from logger import logger
from providers import helpers


class BaseProvider(ABC):

    def __init__(self, loop):
        self.session = aiohttp.ClientSession(loop=loop)
        self.timeout = 10
        self.loop = loop
        self.cookies = {}

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
            return "{}"

    async def execute(self):
        raise NotImplemented
