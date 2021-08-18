import abc
from typing import List
from datetime import timedelta
import asyncio

from .abc import *
from .pair import *

class Controller:
    def __init__(self):
        ''' 
        feeder-downloader对列表，键为id值为Pair
        '''
        self.__pairs = {}

    def validate(self, pair_id: str):
        if pair_id not in self.__pair_list:
            self.__pairs[pair_id] = Pair()

    def add_feeder(self, pair_id: str, feeder: Feeder):
        self.validate(pair_id)
        self.__pairs[pair_id].add_feeder(feeder)

    def add_feeders(self, pair_id: str, feeders: List[Feeder]):
        self.validate(pair_id)
        self.__pairs[pair_id].add_feeders(feeders)

    def add_downloader(self, pair_id: str, downloader: Downloader):
        self.validate(pair_id)
        self.__pairs[pair_id].add_downloader(downloader)

    def add_downloaders(self, pair_id: str, downloaders: List[Downloader]):
        self.validate(pair_id)
        self.__pairs[pair_id].add_downloaders(downloaders)

    def set_timedelta(self, pair_id: str, timedelta: timedelta):
        self.validate(pair_id)
        self.__pairs[pair_id].set_timedelta(timedelta)

    def set_pair(self, pair_id: str, pair: Pair):
        self.__pairs[pair_id] = pair

    def get_pair(self, pair_id: str) -> Pair:
        return self.__pairs[pair_id]

    def run(self):
        for pair_id, pair in self.__pairs.items():
            pass  # TODO
