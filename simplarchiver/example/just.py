import asyncio
import logging
import uuid

from simplarchiver import Downloader


class JustDownloader(Downloader):
    """一个只会输出Item的Downloader"""
    running: int = 0

    def __init__(self, i=uuid.uuid4()):
        """
        i表示Feeder的编号
        """
        self.id = i
        self.log('Initialized')

    def log(self, msg):
        logging.info('JustDownloader %s | %s' % (self.id, msg))

    async def download(self, item):
        self.log('I get an item! %s' % item)
        JustDownloader.running += 1
        self.log('Now there are %d SleepDownloader awaiting including me' % JustDownloader.running)
        item = await asyncio.sleep(delay=0, result=item)
        self.log('For the item %s, time to wake up' % item)
        JustDownloader.running -= 1
        self.log('Now there are %d SleepDownloader awaiting' % JustDownloader.running)
