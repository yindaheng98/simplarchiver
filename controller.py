import abc
from typing import List
from datetime import timedelta


class Feeder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_feeds():
        pass


class Downloader(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def download(item):
        pass


class Pair:
    '''
    feeder-downloader对
    '''

    def __init__(self):
        self.__feeders: List[Feeder] = []
        self.__downloaders: List[Downloader] = []
        # 一次下载全部完成后，经过多长时间开始下一次下载
        self.__timedelta: timedelta = timedelta(minutes=30)
        # 并发数
        self.__concurrency: int = 1

    def add_feeder(self, feeder: Feeder):
        self.__feeders.append(feeder)

    def add_feeders(self, feeders: List[Feeder]):
        self.__feeders.extend(feeders)

    def add_downloader(self, downloader: Downloader):
        self.__downloaders.append(feeder)

    def add_downloaders(self, downloaders: List[Downloader]):
        self.__downloaders.extend(downloaders)

    def set_timedelta(self, timedelta: timedelta):
        self.__timedelta = timedelta

    def set_concurrency(self, n: int):
        self.__concurrency = n

    def run(self, prefix):
        pass


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

    @staticmethod
    def run(pair):
        for id, pair in self.__pairs.items():
            pair.run(id)
