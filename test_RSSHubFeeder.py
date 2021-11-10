import asyncio
import logging
from datetime import timedelta

import httpx

from simplarchiver import Pair
from simplarchiver.example import JustDownloader
from simplarchiver.example.rss import EnclosureOnlyDownloader, EnclosureExceptDownloader
from simplarchiver.example.rss import RSSHubFeeder, RSSHubMultiPageFeeder
from test_secret import rsshub_data, rsshub_multipage_data

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s | %(levelname)-8s | %(name)-26s | %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


rsshub_feeders = [RSSHubFeeder(
    url=rsshub,
    httpx_client_opt_generator=lambda: {
        'timeout': httpx.Timeout(20.0),
        'transport': httpx.AsyncHTTPTransport(retries=10)
    }
) for rsshub in rsshub_data]

rsshub_multipage_feeders = [RSSHubMultiPageFeeder(
    url_gen=rsshub['url_gen'], max_pages=rsshub['max_pages'],
) for rsshub in rsshub_multipage_data]

just_downloaders = [JustDownloader(i) for i in range(1, 4)]
eo_downloaders = [EnclosureOnlyDownloader(base_downloader=JustDownloader(i)) for i in range(4, 7)]
ee_downloaders = [EnclosureExceptDownloader(base_downloader=JustDownloader(i)) for i in range(7, 10)]

pair = Pair(rsshub_feeders + rsshub_multipage_feeders,
            just_downloaders + eo_downloaders + ee_downloaders,
            timedelta(seconds=5), 4, 8)
log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once())
