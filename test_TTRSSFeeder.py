import asyncio
import logging
from datetime import timedelta

import httpx

from simplarchiver import Pair
from simplarchiver.example.rss import TTRSSCatFeeder, TTRSSHubLinkFeeder
from simplarchiver.example import JustDownloader, SubprocessDownloader, JustLogCallbackDownloader
from simplarchiver.example.file import CentralizedUpdateDownloader
from test_secret import ttrss_data

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


ttrss_feeders = [TTRSSHubLinkFeeder(
    TTRSSCatFeeder(
        cat_id=ttrss['cat_id'],
        logger=logging.getLogger("test_TTRSSFeeder %s %d" % (ttrss['url'], ttrss['cat_id'])),
        url=ttrss['url'],
        username=ttrss['username'],
        password=ttrss['password']),
    logger=logging.getLogger("test_TTRSSHubLinkFeeder %s %d" % (ttrss['url'], ttrss['cat_id']))
) for ttrss in ttrss_data]

just_downloaders = [JustDownloader(i) for i in range(1, 4)]

subprocess_downloaders = [
    JustLogCallbackDownloader(
        SubprocessDownloader(
            lambda x: 'ping 127.0.0.1', 'gbk',
            logger=logging.getLogger("test_SubprocessDownloader")),
        logger=logging.getLogger("test_JustLogCallbackDownloader")),
    CentralizedUpdateDownloader(
        base_downloader=SubprocessDownloader(
            lambda x: 'ping 127.0.0.1', 'gbk',
            logger=logging.getLogger("test_SubprocessDownloader")),
        update_list_path="./test.json",
        update_list_pair_gen=lambda i: (i['link'], i['pubDate']) if 'link' in i and 'pubDate' in i else (None, None),
        logger=logging.getLogger("test_UpdateDownloader")
    )
]

pair = Pair(ttrss_feeders,
            just_downloaders + subprocess_downloaders,
            timedelta(seconds=5), 4, 8)
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
