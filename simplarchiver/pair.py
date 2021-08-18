from .abc import *
from typing import List
from datetime import timedelta
import asyncio


class DownloadController:
    '''Download控制器'''

    def __init__(self, downloader: Downloader, buffer_size=100):
        self.__downloader: Downloader = downloader
        self.__queue: asyncio.Queue = asyncio.Queue(buffer_size)

    async def put(self, item):
        '''将待下载的feed item入队列'''
        await self.__queue.put(item)

    async def join(self):
        '''等待队列中的所有任务完成'''
        await self.__queue.join()

    async def get_task(self, sem: asyncio.Semaphore):
        '''独立运行的Download任务'''
        while True:
            item = await self.__queue.get()
            if item is None:
                self.__queue.task_done()
                break  # 用None表示feed结束
            with sem:
                await self.__downloader.download(item)
                self.__queue.task_done()  # task_done配合join可以判断任务是否全部完成


class FeedController:
    '''Feed控制器'''

    def __init__(self, feeder: Feeder):
        self.__feeder: Feeder = feeder

    async def __get_feeds(self, sem: asyncio.Semaphore):
        '''以固定并发数进行self.__feeder.get_feeds()'''
        it = self.__feeder.get_feeds()
        try:
            while True:
                async with sem:  # 不用直接async for就是为了这个在next前面调用的信号量
                    feed = await it.__anext__()
                    yield feed
        except StopAsyncIteration:
            pass

    async def get_task(self, sem: asyncio.Semaphore, download_controllers: List[DownloadController]):
        '''独立运行的Feed任务'''
        async for item in self.__get_feeds(sem):  # 以固定并发数获取待下载项目
            if item is None:
                continue  # None 是退出记号，要从正常的item里面过滤掉
            for dc in download_controllers:  # 每个下载器都要接收到待下载项目
                await dc.put(item)
        for dc in download_controllers:  # 等待下载器的所有下载项目完成后才退出
            await dc.put(None)  # 用None表示feed结束
            await dc.join()


class Pair:
    '''feeder-downloader对'''

    def __init__(self):
        self.__fcs: List[FeedController] = []
        self.__dcs: List[DownloadController] = []

        # 一次下载全部完成后，经过多长时间开始下一次下载
        self.__timedelta: timedelta = timedelta(minutes=30)

        # Semaphore信号量是asyncio提供的控制协程并发数的方法
        self.__fc_sem: asyncio.Semaphore = asyncio.Semaphore(3)
        self.__dc_sem: asyncio.Semaphore = asyncio.Semaphore(3)

        # 每个下载器都需要一个队列
        self.__queues: List[asyncio.Queue] = []

    def add_feeder(self, feeder: Feeder):
        self.__fcs.append(FeedController(feeder))

    def add_feeders(self, feeders: List[Feeder]):
        self.__feeders.extend([FeedController(feeder) for feeder in feeders])

    def add_downloader(self, downloader: Downloader):
        self.__downloaders.append(DownloadController(downloader))

    def add_downloaders(self, downloaders: List[Downloader]):
        self.__downloaders.extend([DownloadController(downloader) for downloader in downloaders])

    def set_timedelta(self, timedelta: timedelta):
        self.__timedelta = timedelta

    def set_feeder_concurrency(self, n: int):
        self.__feeder_sem = asyncio.Semaphore(n)

    def set_downloader_concurrency(self, n: int):
        self.__downloader_sem = asyncio.Semaphore(n)

    def get_tasks(self):
        '''聚合独立运行的Feed&Download任务'''
        tasks = []
        tasks.extend([fc.get_task(self.__fc_sem, self.__dcs) for fc in self.__fcs])
        tasks.extend([dc.get_task(self.__fc_sem) for dc in self.__dcs])
        return tasks

    async def run_once(self):
        await asyncio.gather(self.get_tasks())

    async def run_forever(self):
        while await asyncio.sleep(self.__timedelta.total_seconds(), result=True):
            await self.run_once()
    