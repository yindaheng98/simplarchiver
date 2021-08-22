import asyncio
import logging
from datetime import timedelta

from simplarchiver import Pair
from simplarchiver.example import FileFeeder, DirFeeder, WalkFeeder, JustDownloader

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


ttrss_feeders = [FileFeeder('.'), DirFeeder('.'), WalkFeeder('.')]

just_downloaders = [JustDownloader(i) for i in range(1, 4)]

pair = Pair(ttrss_feeders,
            just_downloaders,
            timedelta(seconds=5), 4, 8)
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
