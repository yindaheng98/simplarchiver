from simplarchiver import Pair
from simplarchiver.example import *
from datetime import timedelta
import logging
import asyncio

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s | %(levelname)-8s | %(name)-26s | %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


pair = Pair([SleepFeeder(0)], [SleepDownloader(0)], timedelta(seconds=5), 4, 4)
for i in range(1, 4):
    pair.add_feeder(SleepFeeder(i))
pair.add_feeders([RandomFilterFeeder(SleepFeeder(i)) for i in range(4, 7)])
for i in range(1, 4):
    pair.add_downloader(SleepDownloader(i))
pair.add_downloaders([RandomFilterDownloader(SleepDownloader(i)) for i in range(4, 7)])
pair.add_downloaders([JustLogCallbackDownloader(SleepDownloader(i)) for i in range(7, 10)])
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
pair.set_downloader_concurrency(6)
pair.set_timedelta(timedelta(seconds=10))
log("pair.coroutine_forever()")
asyncio.run(pair.coroutine_forever())
