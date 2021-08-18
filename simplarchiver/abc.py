import abc
import asyncio


class Feeder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def get_feeds(self):
        yield


class Downloader(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def download(self, item):
        pass
