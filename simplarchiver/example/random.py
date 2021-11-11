import asyncio
import random
import uuid

from simplarchiver import Feeder, Downloader
from simplarchiver import Filter, FilterFeeder, FilterDownloader


class RandomFeeder(Feeder):
    """一个返回随机数的Feeder"""
    running: int = 0

    def __init__(self, i=uuid.uuid4(), n=10, rand_max=5):
        """
        i表示Feeder的编号
        n表示总共要返回多少个item
        如果没有指定seconds，那就睡眠最大rand_max秒的随机时长
        """
        super().__init__()
        self.rand_max = rand_max
        self.n = n
        self.id = i
        self.getLogger().info('Initialized: rand_max=%s, n=%s' % (rand_max, n))

    async def get_feeds(self):
        for i in range(0, self.n):
            RandomFeeder.running += 1
            self.getLogger().info('Now there are %d RandomFeeder awaiting including me' % RandomFeeder.running)
            item = await asyncio.sleep(delay=0.1, result=random.random() * self.rand_max)
            self.getLogger().info('Time to wake up and return an item %s' % item)
            RandomFeeder.running -= 1
            self.getLogger().info('Now there are %d RandomFeeder awaiting' % RandomFeeder.running)
            yield item


class RandomFilter(Filter):
    """一个随机过滤item的Feeder"""

    async def filter(self, item):
        r = random.random()
        self.getLogger().info(
            "rand  a number %f and item %s, " % (r, item) + ("keep the item" if r > 0.5 else "drop the item"))
        return item if r > 0.5 else None


def RandomFilterFeeder(base_feeder: Feeder):
    f = FilterFeeder(base_feeder, RandomFilter())
    f.setTag('RandomFilterFeeder')
    return f


def RandomFilterDownloader(base_downloader: Downloader):
    f = FilterDownloader(base_downloader, RandomFilter())
    f.setTag('RandomFilterDownloader')
    return f
