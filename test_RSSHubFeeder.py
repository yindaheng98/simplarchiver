import asyncio
import logging
from datetime import timedelta

from simplarchiver import Pair
from simplarchiver.example import RSSHubFeeder, TTRSSFeeder, JustDownloader
from test_secret import ttrss_data, rsshub_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


ttrss_feeders = [TTRSSFeeder(
    cat_id=ttrss['cat_id'],
    logger=logging.getLogger("test_TTRSSFeeder %s %d" % (ttrss['url'], ttrss['cat_id'])),
    url=ttrss['url'],
    username=ttrss['username'],
    password=ttrss['password']
) for ttrss in ttrss_data]
rsshub_feeders = [RSSHubFeeder(
    url=rsshub,
    logger=logging.getLogger("test_RSSHubFeeder %s" % rsshub)
) for rsshub in rsshub_data]
pair = Pair(ttrss_feeders + rsshub_feeders,
            [JustDownloader(i) for i in range(1, 4)], timedelta(seconds=5), 4, 4)
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
pair.set_timedelta(timedelta(seconds=10))
