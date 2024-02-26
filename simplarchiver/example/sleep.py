from simplarchiver import Feeder, Downloader, Filter, Amplifier
import random
import asyncio
import logging
import uuid


class SleepFeeder(Feeder):
    """一个只会睡觉的Feeder"""
    running: int = 0

    def __init__(self, i=uuid.uuid4(), n=10, seconds=None, rand_max=1):
        """
        i表示Feeder的编号
        n表示总共要返回多少个item
        如果指定了seconds，每次就睡眠seconds秒
        如果没有指定seconds，那就睡眠最大rand_max秒的随机时长
        """
        super().__init__()
        self.seconds = seconds
        self.rand_max = rand_max
        self.n = n
        self.id = i
        self.getLogger().info('Initialized: seconds=%s, rand_max=%s, n=%s' % (seconds, rand_max, n))

    async def get_feeds(self):
        for i in range(0, self.n):
            t = random.random() * self.rand_max if self.seconds is None else self.seconds
            SleepFeeder.running += 1
            self.getLogger().info('Now there are %d SleepFeeder awaiting including me, I will sleep %f seconds' % (
                SleepFeeder.running, t))
            item = await asyncio.sleep(delay=t, result='item(i=%s,t=%s)' % (i, t))
            self.getLogger().info('I have slept %f seconds, time to wake up and return an item %s' % (t, item))
            SleepFeeder.running -= 1
            self.getLogger().info('I wake up, Now there are %d SleepFeeder awaiting' % SleepFeeder.running)
            yield item


class SleepDownloader(Downloader):
    """一个只会睡觉的Downloader"""
    running: int = 0

    def __init__(self, i=uuid.uuid4(), seconds=None, rand_max=5):
        """
        i表示Feeder的编号
        如果指定了seconds，每次就睡眠seconds秒
        如果没有指定seconds，那就睡眠最大rand_max秒的随机时长
        """
        super().__init__()
        self.seconds = seconds
        self.rand_max = rand_max
        self.id = i
        self.getLogger().info('Initialized: seconds=%s, rand_max=%s' % (seconds, rand_max))
        self.running: int = 0

    async def download(self, item):
        self.getLogger().info('I get an item! %s' % item)
        t = random.random() % self.rand_max if self.seconds is None else self.seconds
        SleepDownloader.running += 1
        self.running += 1
        self.getLogger().info('🟢: Now there are %d SleepDownloader awaiting including %d me, I will sleep %f seconds' % (SleepDownloader.running, self.running, t))
        item = await asyncio.sleep(delay=t, result=item)
        self.getLogger().info('I have slept %f seconds for the item %s, time to wake up' % (t, item))
        self.running -= 1
        SleepDownloader.running -= 1
        self.getLogger().info('🔴: Now there are %d SleepDownloader awaiting including %d me, I will sleep %f seconds' % (SleepDownloader.running, self.running, t))


class SleepFliter(Filter):
    def __init__(self, i=uuid.uuid4()):
        super().__init__()
        self.id = i
        self.getLogger().info('Initialized: filter=%s' % i)

    async def filter(self, item):
        self.getLogger().info('I get an item! %s' % item)
        return item


class SleepAmplifier(Amplifier):
    def __init__(self, i=uuid.uuid4()):
        super().__init__()
        self.id = i
        self.getLogger().info('Initialized: amplify=%s' % i)

    async def amplify(self, item):
        self.getLogger().info('I get an item! %s' % item)
        item += 'a'
        yield item
        item += 'b'
        yield item
        item += 'c'
        yield item
