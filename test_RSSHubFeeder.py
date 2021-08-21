import asyncio
import logging
from datetime import timedelta

import httpx

from simplarchiver import Pair
from simplarchiver.example import RSSHubFeeder, RSSHubMultiPageFeeder, TTRSSCatFeeder, TTRSSHubLinkFeeder
from simplarchiver.example import JustDownloader, SubprocessDownloader, JustLogCallbackDownloader, UpdateDownloader
from simplarchiver.example import EnclosureOnlyDownloader, EnclosureExceptDownloader
from test_secret import ttrss_data, rsshub_data, rsshub_multipage_data

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

rsshub_feeders = [RSSHubFeeder(
    url=rsshub,
    logger=logging.getLogger("test_RSSHubFeeder %s" % rsshub),
    httpx_client_opt_generator=lambda: {
        'timeout': httpx.Timeout(20.0),
        'transport': httpx.AsyncHTTPTransport(retries=10)
    }
) for rsshub in rsshub_data]

rsshub_multipage_feeders = [RSSHubMultiPageFeeder(
    url_gen=rsshub['url_gen'], max_pages=rsshub['max_pages'],
    logger=logging.getLogger("test_RSSHubMultiPageFeeder %s" % rsshub)
) for rsshub in rsshub_multipage_data]

just_downloaders = [JustDownloader(i) for i in range(1, 4)]
eo_downloaders = [EnclosureOnlyDownloader(base_downloader=JustDownloader(i)) for i in range(4, 7)]
ee_downloaders = [EnclosureExceptDownloader(base_downloader=JustDownloader(i)) for i in range(7, 10)]

subprocess_downloaders = [
    JustLogCallbackDownloader(
        SubprocessDownloader(
            lambda x: 'ping 127.0.0.1', 'gbk',
            logger=logging.getLogger("test_SubprocessDownloader")),
        logger=logging.getLogger("test_JustLogCallbackDownloader")),
    UpdateDownloader(
        base_downloader=SubprocessDownloader(
            lambda x: 'ping 127.0.0.1', 'gbk',
            logger=logging.getLogger("test_SubprocessDownloader")),
        update_list_path="./test.json",
        update_list_pair_gen=lambda i: (i['link'], i['pubDate']) if 'link' in i and 'pubDate' in i else (None, None),
        logger=logging.getLogger("test_UpdateDownloader")
    )
]

pair = Pair(ttrss_feeders + rsshub_feeders + rsshub_multipage_feeders,
            just_downloaders + eo_downloaders + ee_downloaders + subprocess_downloaders,
            timedelta(seconds=5), 4, 8)
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
