import asyncio
import logging
from datetime import timedelta

from simplarchiver import Pair
from simplarchiver.example import RSSHubFeeder, RSSHubMultiPageFeeder, TTRSSCatFeeder, JustDownloader, \
    SubprocessDownloader
from test_secret import ttrss_data, rsshub_data, rsshub_multipage_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


ttrss_feeders = [TTRSSCatFeeder(
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

rsshub_multipage_feeders = [RSSHubMultiPageFeeder(
    url_gen=rsshub['url_gen'], max_pages=rsshub['max_pages'],
    logger=logging.getLogger("test_RSSHubMultiPageFeeder %s" % rsshub)
) for rsshub in rsshub_multipage_data]

just_downloaders = [JustDownloader(i) for i in range(1, 4)]


async def callback(item, cmd, returncode):
    log('SubprocessDownloader subprocess exit: %s' % {
        'item': item, 'cmd': cmd, 'returncode': returncode
    })


subprocess_downloaders = [
    SubprocessDownloader(lambda x: 'ping 127.0.0.1', callback, 'gbk',
                         logger=logging.getLogger("test_SubprocessDownloader"))
]

pair = Pair(ttrss_feeders + rsshub_feeders + rsshub_multipage_feeders,
            just_downloaders + subprocess_downloaders,
            timedelta(seconds=5), 4, 4)
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
