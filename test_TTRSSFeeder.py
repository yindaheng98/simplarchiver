import os
import asyncio
import logging
from datetime import timedelta
from urllib.parse import urlparse

from simplarchiver import Pair
from simplarchiver.example import JustDownloader, SubprocessDownloader, JustLogCallbackDownloader
from simplarchiver.example.file import CentralizedUpdateDownloader, DecentralizedUpdateDownloader
from simplarchiver.example.rss import TTRSSCatFeeder, TTRSSHubLinkFeeder
from test_secret import ttrss_data

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s | %(levelname)-8s | %(name)-26s | %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


ttrss_feeders = [TTRSSHubLinkFeeder(
    TTRSSCatFeeder(
        cat_id=ttrss['cat_id'],
        url=ttrss['url'],
        username=ttrss['username'],
        password=ttrss['password']
    )
) for ttrss in ttrss_data]

just_downloaders = [JustDownloader(i) for i in range(1, 4)]

subprocess_downloaders = [
    JustLogCallbackDownloader(
        SubprocessDownloader(
            lambda x: 'ping 127.0.0.1', 'gbk')),
    CentralizedUpdateDownloader(
        base_downloader=SubprocessDownloader(lambda x: 'ping 127.0.0.1', 'gbk'),
        update_list_path="./test/test.json",
        update_list_pair_gen=lambda i: (i['link'], i['pubDate']) if 'link' in i and 'pubDate' in i else (None, None)
    )
]


def rsshub_update_list_pair_gen(i):
    k = None
    v = None
    if 'link' in i:
        url = urlparse(i['link'])
        k = os.path.join(url.netloc, url.path.replace("/", "⧸") + '.txt')
    if 'pubDate' in i:
        v = i['pubDate']
    return k, v


decentralized_downloaders = [
    DecentralizedUpdateDownloader(
        base_downloader=SubprocessDownloader(lambda x: 'ping 127.0.0.1', 'gbk'),
        update_list_path="./test/ttrss",
        update_list_pair_gen=rsshub_update_list_pair_gen
    )
]

pair = Pair(ttrss_feeders,
            just_downloaders + subprocess_downloaders + decentralized_downloaders,
            timedelta(seconds=1), timedelta(seconds=5), 4, 8)
pair.setTag("test_UpdateDownloader")
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
