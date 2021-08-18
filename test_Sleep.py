import asyncio
import logging

from simplarchiver.example import SleepFeeder, SleepDownloader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log(msg):
    logging.info('test_Sleep | %s' % msg)


sf = SleepFeeder()


async def test_get_feeds():
    async for item in sf.get_feeds():
        log('get an item: %s' % item)


asyncio.run(test_get_feeds())

sd = SleepDownloader()


async def test_download():
    async for item in sf.get_feeds():
        log('get an item: %s' % item)
        asyncio.create_task(sd.download(item))


asyncio.run(test_download())
