import asyncio
import logging
from datetime import timedelta

from simplarchiver import Pair, AmplifierFeeder
from simplarchiver.example import JustDownloader, ExceptionFeederFilter
from simplarchiver.example.rss import TTRSSCatFeeder, RSSHubFeeder
from test_secret import ttrss_amp_data as ttrss

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s | %(levelname)-8s | %(name)-26s | %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


def ampl_feeder_gen(item):
    return ExceptionFeederFilter(RSSHubFeeder(item['link']), rate=0.2)


ttrss_amp_feeders = [
    AmplifierFeeder(
        ExceptionFeederFilter(
            TTRSSCatFeeder(
                cat_id=ttrss['cat_id'],
                url=ttrss['url'],
                username=ttrss['username'],
                password=ttrss['password']
            ), rate=0.2
        ), ampl_feeder_gen
    )
]

just_downloaders = [JustDownloader(i) for i in range(1, 4)]

pair = Pair(ttrss_amp_feeders,
            just_downloaders,
            timedelta(seconds=5), 4, 8)
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
