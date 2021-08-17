import abc
from typing import List
from datetime import timedelta
import asyncio


class Feeder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def get_feeds():
        yield


class Downloader(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def download(item):
        pass


class DownloadController:
    '''下载控制器'''

    def __init__(self, downloader: Downloader, buffer_size=100):
        self.__downloader: Downloader = downloader
        self.__queue: asyncio.Queue = asyncio.Queue(buffer_size)

    async def put(self, item):
        '''将待下载的feed item入队列'''
        await self.__queue.put(item)

    async def join(self):
        '''等待队列中的所有任务完成'''
        await self.__queue.join()

    async def download_task(self, sem: asyncio.Semaphore):
        '''独立运行的下载任务'''
        while True:
            item = await self.__queue.get()
            with sem:
                await self.__downloader.download(item)
                self.__queue.task_done() # task_done配合join可以判断任务是否全部完成


class FeedController:
    '''Feed控制器'''

    def __init__(self, feeder: Feeder):
        self.__feeder: Feeder = feeder

    def __get_feeds(self, sem: asyncio.Semaphore):
        '''以固定并发数进行self.__feeder.get_feeds()'''
        pass # TODO

    async def feed_task(self, sem: asyncio.Semaphore, download_controllers: List[DownloadController]):
        '''独立运行的Feed任务'''
        async for item in self.__feeder.get_feeds(sem): # 获取待下载项目
            for dc in download_controllers: # 每个下载器都要接收到待下载项目
                await dc.put(item)
        for dc in download_controllers: # 等待下载器的所有下载项目完成后才退出
            await dc.join()


class Pair:
    '''feeder-downloader对'''

    def __init__(self):
        self.__feeders: List[Feeder] = []
        self.__downloaders: List[Downloader] = []

        # 一次下载全部完成后，经过多长时间开始下一次下载
        self.__timedelta: timedelta = timedelta(minutes=30)

        # Semaphore信号量是asyncio提供的控制协程并发数的方法
        self.__feeder_sem: asyncio.Semaphore = asyncio.Semaphore(3)
        self.__downloader_sem: asyncio.Semaphore = asyncio.Semaphore(3)

        # 每个下载器都需要一个队列
        self.__queues: List[asyncio.Queue] = []

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

    def set_feeder_concurrency(self, n: int):
        self.__feeder_sem = asyncio.Semaphore(n)

    def set_downloader_concurrency(self, n: int):
        self.__downloader_sem = asyncio.Semaphore(n)

    async def get_task():
        '''独立运行的Feed&Download任务'''
        pass # TODO


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
            pass # TODO
