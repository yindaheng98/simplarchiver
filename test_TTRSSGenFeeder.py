import asyncio
import logging
import httpx
from datetime import timedelta

from simplarchiver import Pair
from simplarchiver.example import JustDownloader, SubprocessDownloader, JustLogCallbackDownloader
from simplarchiver.example.file import CentralizedUpdateDownloader
from simplarchiver.example.rss import TTRSSGenFeeder
from test_secret import ttrss_gen_url

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s | %(levelname)-8s | %(name)-26s | %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


ttrss_feeders = [TTRSSGenFeeder(ttrss_gen_url, lambda: {
    'timeout': httpx.Timeout(30.0),
    'transport': httpx.AsyncHTTPTransport(retries=5)
})]

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
            timedelta(seconds=1), timedelta(seconds=5), 4, 8)
pair.setTag("test_UpdateDownloader")
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
