from simplarchiver import Controller, Pair
from simplarchiver.example import RandomFeeder, JustDownloader
from datetime import timedelta
import logging
import asyncio

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s | %(levelname)-8s | %(name)-26s | %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


controller = Controller()
for i in range(1, 4):
    controller.add_pair(
        Pair([RandomFeeder('(%d,%d)' % (i, j)) for j in range(1, 4)],
             [JustDownloader('(%d,%d)' % (i, j)) for j in range(1, 4)],
             timedelta(seconds=i * 5), i, i))
asyncio.run(controller.coroutine())
