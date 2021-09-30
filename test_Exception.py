from simplarchiver import Pair
from simplarchiver.example import *
from datetime import timedelta
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


def TestSleepFeeder(i):
    return ExceptionFeederFilter(SleepFeeder(i), rate=0.2)


def TestSleepDownloader(i):
    return ExceptionDownloaderFilter(SleepDownloader(i), rate=0.2)


pair = Pair([TestSleepFeeder(0)], [TestSleepDownloader(0)], timedelta(seconds=5), 4, 4)
for i in range(1, 4):
    pair.add_feeder(TestSleepFeeder(i))
pair.add_feeders([RandomFilterFeeder(TestSleepFeeder(i)) for i in range(4, 7)])
for i in range(1, 4):
    pair.add_downloader(TestSleepDownloader(i))
pair.add_downloaders([RandomFilterDownloader(TestSleepDownloader(i)) for i in range(4, 7)])
pair.add_downloaders([JustLogCallbackDownloader(TestSleepDownloader(i)) for i in range(7, 10)])
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
pair.set_downloader_concurrency(6)
pair.set_timedelta(timedelta(seconds=10))
log("pair.coroutine_forever()")
asyncio.run(pair.coroutine_forever())
