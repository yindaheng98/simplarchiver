import logging
import random
import uuid

from simplarchiver import Callback, CallbackDownloader, FilterCallbackDownloader
from simplarchiver import Feeder, Downloader
from simplarchiver import Filter, FilterFeeder, FilterDownloader


class ExceptionFilter(Filter):
    """一个只会卡bug的Filter"""

    async def filter(self, item):
        p = random.random()
        if p < self.rate:
            raise ValueError("Feeder Exception: %f < %f" % (p, self.rate))
        else:
            self.log('Feeder ok: %f >= %f' % (p, self.rate))
            return item

    def __init__(self, i=uuid.uuid4(), rate=0.5):
        """
        i表示编号
        rate表示以多高的概率抛出错误
        """
        self.rate = rate
        self.id = i
        self.log('Initialized: rate=%f' % rate)

    def log(self, msg):
        logging.info('ExceptionFilter   %s | %s' % (self.id, msg))


def ExceptionFeederFilter(base_feeder: Feeder, i=uuid.uuid4(), rate=0.5):
    return FilterFeeder(base_feeder, ExceptionFilter(i, rate))


def ExceptionDownloaderFilter(base_downloader: Downloader, i=uuid.uuid4(), rate=0.5):
    return FilterDownloader(base_downloader, ExceptionFilter(i, rate))


class ExceptionCallback(Callback):
    """一个只会卡bug的Callback"""

    async def callback(self, item, return_code):
        p = random.random()
        if p < self.rate:
            raise ValueError("Exception: %f < %f" % (p, self.rate))
        else:
            self.log('OK: %f >= %f' % (p, self.rate))
            return item

    def __init__(self, i=uuid.uuid4(), rate=0.5):
        """
        i表示编号
        rate表示以多高的概率抛出错误
        """
        self.rate = rate
        self.id = i
        self.log('Initialized: rate=%f' % rate)

    def log(self, msg):
        logging.info('ExceptionCallback %s | %s' % (self.id, msg))


def ExceptionDownloaderCallback(base_downloader: Downloader, i=uuid.uuid4(), rate=0.5):
    return CallbackDownloader(base_downloader, ExceptionCallback(i, rate))


def ExceptionDownloaderFilterCallback(base_downloader: Downloader, i=uuid.uuid4(), rate=0.5):
    return FilterCallbackDownloader(base_downloader, ExceptionFilter(i, rate), ExceptionCallback(i, rate))
