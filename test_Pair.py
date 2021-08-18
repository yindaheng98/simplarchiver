from simplarchiver import Pair
from simplarchiver.example import SleepFeeder, SleepDownloader
from datetime import timedelta
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


pair = Pair()
for i in range(1, 4):
    pair.add_feeder(SleepFeeder(i))
pair.add_feeders([SleepFeeder(i) for i in range(4, 7)])
# asyncio.run(pair.run_once())
for i in range(1, 4):
    pair.add_downloader(SleepDownloader(i))
pair.add_downloaders([SleepDownloader(i) for i in range(4, 7)])
asyncio.run(pair.run_once())
