import asyncio
import logging
import uuid

from simplarchiver import Downloader, CallbackDownloader


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
        item = await asyncio.sleep(delay=0.1, result=item)
        self.log('For the item %s, time to wake up' % item)
        JustDownloader.running -= 1
        self.log('Now there are %d SleepDownloader awaiting' % JustDownloader.running)


class JustLogCallbackDownloader(CallbackDownloader):
    """只是把Callback的内容输出到log而已"""

    def __init__(self, base_downloader: Downloader,
                 logger: logging.Logger = logging.getLogger("JustLogCallbackDownloader")):
        super(JustLogCallbackDownloader, self).__init__(base_downloader)
        self.__logger = logger

    async def callback(self, item, return_code):
        self.__logger.info(
            "JustLogCallbackDownloader run its callback, return_code: %s, item: %s" % (return_code, item))
