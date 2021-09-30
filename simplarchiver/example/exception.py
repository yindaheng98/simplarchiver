import asyncio
import logging
import random
import uuid

from simplarchiver import FilterFeeder, FilterDownloader, Feeder, Downloader


class ExceptionFeederFilter(FilterFeeder):
    """一个只会卡bug的FeederFilter"""

    async def filter(self, item):
        p = random.random()
        if p < self.rate:
            raise ValueError("    Feeder Exception: %f < %f" % (p, self.rate))
        else:
            self.log('    Feeder ok: %f >= %f' % (p, self.rate))
            return item

    def __init__(self, base_feeder: Feeder, i=uuid.uuid4(), rate=0.5):
        """
        i表示编号
        rate表示以多高的概率抛出错误
        """
        super().__init__(base_feeder)
        self.rate = rate
        self.id = i
        self.log('Initialized: rate=%f' % rate)

    def log(self, msg):
        logging.info('ExceptionFeederFilter     %s | %s' % (self.id, msg))


class ExceptionDownloaderFilter(FilterDownloader):
    """一个只会卡bug的DownloaderFilter"""

    async def filter(self, item):
        p = random.random()
        if p < self.rate:
            raise ValueError("Downloader Exception: %f < %f" % (p, self.rate))
        else:
            self.log('Downloader ok: %f >= %f' % (p, self.rate))
            return item

    def __init__(self, base_downloader: Downloader, i=uuid.uuid4(), rate=0.5):
        """
        i表示编号
        rate表示以多高的概率抛出错误
        """
        super().__init__(base_downloader)
        self.rate = rate
        self.id = i
        self.log('Initialized: rate=%f' % rate)

    def log(self, msg):
        logging.info('ExceptionDownloaderFilter %s | %s' % (self.id, msg))
