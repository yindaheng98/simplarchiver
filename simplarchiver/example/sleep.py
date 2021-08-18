from simplarchiver import Feeder, Downloader
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
        self.seconds = seconds
        self.rand_max = rand_max
        self.n = n
        self.id = i
        self.log('Initialized: seconds=%s, rand_max=%s, n=%s' % (seconds, rand_max, n))

    def log(self, msg):
        logging.info('SleepFeeder     %s | %s' % (self.id, msg))

    async def get_feeds(self):
        for i in range(0, self.n):
            t = random.random() * self.rand_max if self.seconds is None else self.seconds
            SleepFeeder.running += 1
            self.log('Now there are %d SleepFeeder awaiting including me, I will sleep %f seconds' % (SleepFeeder.running, t))
            item = await asyncio.sleep(delay=t, result='item(i=%s,t=%s)' % (i, t))
            self.log('I have slept %f seconds, time to wake up and return an item %s' % (t, item))
            SleepFeeder.running -= 1
            self.log('I wake up, Now there are %d SleepFeeder awaiting' % SleepFeeder.running)
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
        self.seconds = seconds
        self.rand_max = rand_max
        self.id = i
        self.log('Initialized: seconds=%s, rand_max=%s' % (seconds, rand_max))

    def log(self, msg):
        logging.info('SleepDownloader %s | %s' % (self.id, msg))

    async def download(self, item):
        self.log('I get an item! %s' % item)
        t = random.random() % self.rand_max if self.seconds is None else self.seconds
        SleepDownloader.running += 1
        self.log('Now there are %d SleepDownloader awaiting including me, I will sleep %f seconds' % (SleepDownloader.running, t))
        item = await asyncio.sleep(delay=t, result=item)
        self.log('I have slept %f seconds for the item %s, time to wake up' % (t, item))
        SleepDownloader.running -= 1
        self.log('I wake up, Now there are %d SleepDownloader awaiting' % SleepDownloader.running)
