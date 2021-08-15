import abc
from typing import List
from datetime import timedelta


class Feeder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_feeds():
        pass


class Downloader(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def download():
        pass


class Controller:
    def __init__(self):
        self.__pair_list = {}
        # feeder-downloader对列表，形如{ 'idxxxxx': { 'feeders': [ feeder1, feeder2, ... ], 'downloaders': [ downloader1, downloader2, ... ] }] }

    def validate(self):
        if pair_id not in self.__pair_list:
            self.__pair_list[pair_id] = {'feeders': [], 'downloaders': []}
        if 'feeders' not in self.__pair_list[pair_id]:
            self.__pair_list[pair_id]['feeders'] = []
        if 'downloaders' not in self.__pair_list[pair_id]:
            self.__pair_list[pair_id]['downloaders'] = []
        if 'timedelta' not in self.__pair_list[pair_id]:
            self.__pair_list[pair_id]['timedelta'] = timedelta(minutes=30)

    def __add_feeder(self, pair_id: str, feeder: Feeder):
        self.__pair_list[pair_id]['feeders'].append(feeder)

    def __add_downloader(self, pair_id: str, downloader: Downloader):
        self.__pair_list[pair_id]['downloaders'].append(feeder)

    def __set_timedelta(self, pair_id: str, timedelta: timedelta):
        self.__pair_list[pair_id]['timedelta'] = timedelta

    def add_feeder(self, pair_id: str, feeder: Feeder):
        self.validate()
        self.__add_feeder(pair_id, feeder)

    def add_feeders(self, pair_id: str, feeders: List[Feeder]):
        self.validate()
        for feeder in feeders:
            self.__add_feeder(pair_id, feeder)

    def add_downloader(self, pair_id: str, downloader: Downloader):
        self.validate()
        self.__add_downloader(pair_id, feeder)

    def add_downloaders(self, pair_id: str, downloaders: List[Downloader]):
        for downloader in downloaders:
            self.__add_downloader(pair_id, feeder)

    # 一次下载全部完成后，经过多长时间开始下一次下载
    def set_timedelta(self, pair_id: str, timedelta: timedelta):
        self.validate()
        self.__set_timedelta(pair_id, timedelta)
