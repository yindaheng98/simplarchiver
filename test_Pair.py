from simplarchiver import Pair
from simplarchiver.example import SleepFeeder, SleepDownloader
from datetime import timedelta
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


sf = SleepFeeder()
sd = SleepDownloader()


async def test_get_feeds():
    async for item in sf.get_feeds():
        log('get an item: %s' % item)


asyncio.run(test_get_feeds())
