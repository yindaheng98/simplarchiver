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
            self.getLogger().info('Feeder ok: %f >= %f' % (p, self.rate))
            return item

    def __init__(self, i=uuid.uuid4(), rate=0.5):
        """
        i表示编号
        rate表示以多高的概率抛出错误
        """
        super().__init__()
        self.rate = rate
        self.id = i
        self.getLogger().info('Initialized: rate=%f' % rate)


def ExceptionFilterFeeder(base_feeder: Feeder, i=uuid.uuid4(), rate=0.5):
    f = FilterFeeder(base_feeder, ExceptionFilter(i, rate))
    f.setTag('ExceptionFeederFilter')
    return FilterFeeder(base_feeder, ExceptionFilter(i, rate))


def ExceptionFilterDownloader(base_downloader: Downloader, i=uuid.uuid4(), rate=0.5):
    f = FilterDownloader(base_downloader, ExceptionFilter(i, rate))
    f.setTag('ExceptionDownloaderFilter')
    return f


class ExceptionCallback(Callback):
    """一个只会卡bug的Callback"""

    async def callback(self, item, return_code):
        p = random.random()
        if p < self.rate:
            raise ValueError("Exception: %f < %f" % (p, self.rate))
        else:
            self.getLogger().info('OK: %f >= %f' % (p, self.rate))
            return item

    def __init__(self, i=uuid.uuid4(), rate=0.5):
        """
        i表示编号
        rate表示以多高的概率抛出错误
        """
        super().__init__()
        self.rate = rate
        self.id = i
        self.getLogger().info('Initialized: rate=%f' % rate)


def ExceptionCallbackDownloader(base_downloader: Downloader, i=uuid.uuid4(), rate=0.5):
    f = CallbackDownloader(base_downloader, ExceptionCallback(i, rate))
    f.setTag('ExceptionCallbackDownloader')
    return f


def ExceptionFilterCallbackDownloader(base_downloader: Downloader, i=uuid.uuid4(), rate=0.5):
    f = FilterCallbackDownloader(base_downloader, ExceptionFilter(i, rate), ExceptionCallback(i, rate))
    f.setTag('ExceptionFilterCallbackDownloader')
    return f
