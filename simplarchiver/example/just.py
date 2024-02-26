import asyncio
import uuid

from simplarchiver import Downloader, Callback, CallbackDownloader


class JustDownloader(Downloader):
    """一个只会输出Item的Downloader"""
    running: int = 0

    def __init__(self, i=uuid.uuid4()):
        """
        i表示Feeder的编号
        """
        super().__init__()
        self.id = i
        self.getLogger().info('Initialized')
        self.running: int = 0

    async def download(self, item):
        self.getLogger().info('I get an item! %s' % item)
        JustDownloader.running += 1
        self.running += 1
        self.getLogger().info('🟢: Now there are %d SleepDownloader awaiting including %d me' % (JustDownloader.running, self.running))
        item = await asyncio.sleep(delay=0.1, result=item)
        self.getLogger().info('For the item %s, time to wake up' % item)
        self.running -= 1
        JustDownloader.running -= 1
        self.getLogger().info('🔴: Now there are %d SleepDownloader awaiting including %d me' % (JustDownloader.running, self.running))


class JustLogCallback(Callback):
    """只是把Callback的内容输出到log而已"""

    async def callback(self, item, return_code):
        self.getLogger().info(
            "JustLogCallbackDownloader run its callback, return_code: %s, item: %s" % (return_code, item))


def JustLogCallbackDownloader(base_downloader: Downloader):
    f = CallbackDownloader(base_downloader, JustLogCallback())
    f.setTag('JustLogCallbackDownloader')
    return f
