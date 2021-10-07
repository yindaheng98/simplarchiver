from .abc import *
from typing import List
from datetime import timedelta
import asyncio
import logging


class DownloadController:
    """Download控制器"""

    __ID: int = 0

    def __init__(self, downloader: Downloader, buffer_size=100):
        self.__downloader: Downloader = downloader
        self.__buffer_size = buffer_size
        self.__queue: asyncio.Queue = None
        self.__id: int = DownloadController.__ID
        self.__logger = logging.getLogger("DownloadController %d" % self.__id)
        DownloadController.__ID += 1

    async def put(self, item):
        """将待下载的feed item入队列"""
        self.__logger.debug(' start put item: %s' % item)
        await self.__queue.put(item)
        self.__logger.debug('finish put item: %s' % item)

    async def join(self):
        """等待队列中的所有任务完成"""
        self.__logger.debug(' start join coroutine')
        await self.__queue.join()
        self.__logger.debug('finish join coroutine')

    async def coroutine(self, sem: asyncio.Semaphore):
        """独立运行的Download任务"""
        self.__queue: asyncio.Queue = asyncio.Queue(self.__buffer_size)
        # 运行时生成asyncio.Queue
        # asyncio相关数据结构必须在asyncio.run之后生成，否则会出现错误：
        # got Future <Future pending> attached to a different loop
        # 这是由于asyncio.run会生成新的事件循环，不同事件循环中的事件不能互相调用
        self.__logger.debug('coroutine | start')
        while True:
            self.__logger.debug('coroutine | wait for an item')
            item = await self.__queue.get()
            self.__logger.debug('coroutine | get an item            : %s' % item)
            if item is None:
                self.__queue.task_done()
                break  # 用None表示feed结束
            async with sem:
                self.__logger.debug('coroutine | start download item    : %s' % item)
                try:
                    await self.__downloader.download(item)
                except Exception:
                    self.__logger.exception('Catch an Exception from your Downloader:')
                self.__logger.debug('coroutine | finish download item   : %s' % item)
                self.__queue.task_done()  # task_done配合join可以判断任务是否全部完成
        self.__logger.debug('coroutine | end')


class FeedController:
    """Feed控制器"""

    __ID: int = 0

    def __init__(self, feeder: Feeder):
        self.__feeder: Feeder = feeder
        self.__id: int = FeedController.__ID
        self.__logger = logging.getLogger("FeedController %d" % self.__id)
        FeedController.__ID += 1

    async def __get_feeds(self, sem: asyncio.Semaphore):
        """以固定并发数进行self.__feeder.get_feeds()"""
        try:
            self.__logger.debug('get_feeds | starting iter')
            it = self.__feeder.get_feeds()
            self.__logger.debug('get_feeds | iter started')
            while True:
                self.__logger.debug('get_feeds | wait for sem')
                async with sem:  # 不直接用async for就是为了这个在next前面调用的信号量
                    self.__logger.debug('get_feeds | sem got, wait for next feed')
                    feed = await it.__anext__()
                    self.__logger.debug('get_feeds | feed got: %s' % feed)
                    yield feed
        except StopAsyncIteration:
            self.__logger.debug('get_feeds | iter exited')
            pass
        except Exception:  # 如果出错其他错直接退出
            self.__logger.exception('Catch an Exception from your Feeder:')
            return

    async def coroutine(self, sem: asyncio.Semaphore, download_controllers: List[DownloadController]):
        """独立运行的Feed任务"""
        self.__logger.debug('coroutine | start')
        async for item in self.__get_feeds(sem):  # 以固定并发数获取待下载项目
            self.__logger.debug('coroutine | get an item: %s' % item)
            if item is None:
                continue  # None 是退出记号，要从正常的item里面过滤掉
            for dc in download_controllers:  # 每个下载器都要接收到待下载项目
                self.__logger.debug('coroutine | start put item into queue : %s' % item)
                await dc.put(item)
                self.__logger.debug('coroutine | finish put item into queue: %s' % item)
            self.__logger.debug('coroutine | wait for next item')
        self.__logger.debug('coroutine | end')


class Pair:
    """feeder-downloader对"""

    __ID: int = 0

    def __init__(self,
                 feeders: List[Feeder] = [],
                 downloaders: List[Downloader] = [],
                 time_delta: timedelta = timedelta(minutes=30),
                 feeder_concurrency: int = 3,
                 downloader_concurrency: int = 3):
        self.__fcs: List[FeedController] = []
        self.__dcs: List[DownloadController] = []
        self.add_feeders(feeders)
        self.add_downloaders(downloaders)

        # 一次下载全部完成后，经过多长时间开始下一次下载
        self.__timedelta: timedelta = time_delta

        # Semaphore信号量是asyncio提供的控制协程并发数的方法
        self.__fc_concurrency: int = feeder_concurrency
        self.__dc_concurrency: int = downloader_concurrency

        # 每个下载器都需要一个队列
        self.__queues: List[asyncio.Queue] = []

        self.__id: int = Pair.__ID
        self.__logger = logging.getLogger("Pair %d" % self.__id)
        Pair.__ID += 1

    def add_feeder(self, feeder: Feeder):
        self.__fcs.append(FeedController(feeder))

    def add_feeders(self, feeders: List[Feeder]):
        self.__fcs.extend([FeedController(feeder) for feeder in feeders])

    def add_downloader(self, downloader: Downloader):
        self.__dcs.append(DownloadController(downloader))

    def add_downloaders(self, downloaders: List[Downloader]):
        self.__dcs.extend([DownloadController(downloader) for downloader in downloaders])

    def set_timedelta(self, timedelta: timedelta):
        self.__timedelta = timedelta

    def set_feeder_concurrency(self, n: int):
        self.__fc_concurrency = n

    def set_downloader_concurrency(self, n: int):
        self.__dc_concurrency = n

    def __log_coroutine_once(self, msg):
        self.__logger.debug("coroutine_once | %s" % msg)

    async def coroutine_once(self):
        """运行一次Feed&Download任务"""

        fc_sem = asyncio.Semaphore(self.__fc_concurrency)
        dc_sem = asyncio.Semaphore(self.__dc_concurrency)
        # 运行时生成asyncio.Semaphore
        # asyncio相关数据结构必须在asyncio.run之后生成，否则会出现错误：
        # got Future <Future pending> attached to a different loop
        # 这是由于asyncio.run会生成新的事件循环，不同事件循环中的事件不能互相调用

        self.__log_coroutine_once('feeder     tasks | start  creating')
        # Download任务开始之后是一直在运行的，等到Feed任务给他发停止信息才会停
        for dc in self.__dcs:
            asyncio.create_task(dc.coroutine(dc_sem))
        self.__log_coroutine_once('feeder     tasks | finish creating')

        self.__log_coroutine_once('feeder     tasks | start')
        # 聚合独立运行的Feed任务
        await asyncio.gather(*[fc.coroutine(fc_sem, self.__dcs) for fc in self.__fcs])
        self.__log_coroutine_once('feeder     tasks | end')

        self.__log_coroutine_once('downloader tasks | start  sending stop signal')
        # Feed全部结束后向Download任务发送停止信号
        for dc in self.__dcs:
            await dc.put(None)  # 用None表示feed结束
        self.__log_coroutine_once('downloader tasks | finish sending stop signal')

        self.__log_coroutine_once('downloader tasks | start  join')
        for dc in self.__dcs:  # 等待下载器的所有下载项目完成后才退出
            await dc.join()
        self.__log_coroutine_once('downloader tasks | finish join')

    async def __coroutine_once_no_raise(self):
        self.__log_coroutine_once('start')
        while True:
            try:
                await asyncio.create_task(self.coroutine_once())
                self.__log_coroutine_once('end')
                return
            except Exception:
                logging.exception('Catch an Exception from Pair:')
                self.__log_coroutine_once('retry')

    async def coroutine_forever(self):
        await self.__coroutine_once_no_raise()
        self.__logger.debug('sleep for %ss before next coroutine_once' % self.__timedelta.total_seconds())
        while await asyncio.sleep(self.__timedelta.total_seconds(), result=True):
            await self.__coroutine_once_no_raise()
            self.__logger.debug('sleep for %ss before next coroutine_once' % self.__timedelta.total_seconds())
