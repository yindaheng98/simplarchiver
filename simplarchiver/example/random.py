import asyncio
import logging
import random
import uuid

from simplarchiver import Feeder


class RandomFeeder(Feeder):
    """一个返回随机数的Feeder"""
    running: int = 0

    def __init__(self, i=uuid.uuid4(), n=10, rand_max=5):
        """
        i表示Feeder的编号
        n表示总共要返回多少个item
        如果没有指定seconds，那就睡眠最大rand_max秒的随机时长
        """
        self.rand_max = rand_max
        self.n = n
        self.id = i
        self.log('Initialized: rand_max=%s, n=%s' % (rand_max, n))

    def log(self, msg):
        logging.info('RandomFeeder    %s | %s' % (self.id, msg))

    async def get_feeds(self):
        for i in range(0, self.n):
            RandomFeeder.running += 1
            self.log('Now there are %d RandomFeeder awaiting including me' % RandomFeeder.running)
            item = await asyncio.sleep(delay=0.1, result=random.random() * self.rand_max)
            self.log('Time to wake up and return an item %s' % item)
            RandomFeeder.running -= 1
            self.log('Now there are %d RandomFeeder awaiting' % RandomFeeder.running)
            yield item