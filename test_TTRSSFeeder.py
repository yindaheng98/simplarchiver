import asyncio
import logging
from datetime import timedelta

from simplarchiver import Pair
from simplarchiver.example import JustDownloader, SubprocessDownloader, JustLogCallbackDownloader
from simplarchiver.example.file import CentralizedUpdateDownloader
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
        update_list_path="./test.json",
        update_list_pair_gen=lambda i: (i['link'], i['pubDate']) if 'link' in i and 'pubDate' in i else (None, None)
    )
]

pair = Pair(ttrss_feeders,
            just_downloaders + subprocess_downloaders,
            timedelta(seconds=5), 4, 8)
pair.setTag("test_UpdateDownloader")
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
