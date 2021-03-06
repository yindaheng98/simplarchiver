from simplarchiver import Pair, Logger
from simplarchiver.example import *
from datetime import timedelta
import logging
import asyncio

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s | %(levelname)-8s | %(name)-26s | %(message)s')

def log(msg):
    logging.info('test_Pair | %s' % msg)


def TestSleepFeeder(i):
    return ExceptionFilterFeeder(SleepFeeder(i), rate=0.2)


def TestSleepDownloader(i):
    return ExceptionFilterDownloader(
        ExceptionCallbackDownloader(
            ExceptionFilterCallbackDownloader(
                SleepDownloader(i),
                rate=0.2),
            rate=0.2),
        rate=0.2)


pair = Pair([TestSleepFeeder(0)], [TestSleepDownloader(0)], timedelta(seconds=1), timedelta(seconds=5), 4, 4)
for i in range(1, 4):
    pair.add_feeder(TestSleepFeeder(i))
pair.add_feeders([RandomFilterFeeder(TestSleepFeeder(i)) for i in range(4, 7)])
for i in range(1, 4):
    pair.add_downloader(TestSleepDownloader(i))
pair.setTag('Tag after add')
pair.add_downloaders([RandomFilterDownloader(TestSleepDownloader(i)) for i in range(4, 7)])
pair.setTag(None)
pair.add_downloaders([JustLogCallbackDownloader(TestSleepDownloader(i)) for i in range(7, 10)])
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
pair.set_downloader_concurrency(6)
pair.set_interval(timedelta(seconds=10))
log("pair.coroutine_forever()")
asyncio.run(pair.coroutine_forever())
