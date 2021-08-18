from simplarchiver import Controller, Pair
from simplarchiver.example import RandomFeeder, JustDownloader
from datetime import timedelta
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


controller = Controller()
for i in range(1, 4):
    pair = Pair()
    pair.add_feeders([RandomFeeder('(%d,%d)' % (i, j)) for j in range(1, 4)])
    pair.add_downloaders([JustDownloader('(%d,%d)' % (i, j)) for j in range(1, 4)])
    pair.set_downloader_concurrency(i)
    pair.set_timedelta(timedelta(seconds=i * 5))
    controller.add_pair(pair)
asyncio.run(controller.coroutine())
