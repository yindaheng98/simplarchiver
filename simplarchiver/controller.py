from .pair import *
from typing import List


class Controller:
    def __init__(self, pairs: List[Pair] = []):
        """
        feeder-downloader对列表，键为id值为Pair
        每个Pair都是独立运行的
        """
        self.__pairs = []
        self.add_pairs(pairs)

    def add_pair(self, pair: Pair):
        self.__pairs.append(pair)

    def add_pairs(self, pairs: List[Pair]):
        self.__pairs.extend(pairs)

    async def coroutine(self):
        await asyncio.gather(*[pair.coroutine_forever() for pair in self.__pairs])
