import asyncio
import logging
import time

import httpx

from simplarchiver import Pair, MultiRoot, Branch
from simplarchiver.example import JustDownloader
from simplarchiver.example.rss import EnclosureOnlyDownloader, EnclosureExceptDownloader
from simplarchiver.example.rss import RSSHubFeeder, RSSHubMultiPageFeeder
from test_secret import rsshub_data, rsshub_multipage_data

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s | %(levelname)-8s | %(name)-26s | %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


root = MultiRoot()
rsshub_feeders = [root.next(RSSHubFeeder(
    url=rsshub,
    httpx_client_opt_generator=lambda: {
        'timeout': httpx.Timeout(20.0),
        'transport': httpx.AsyncHTTPTransport(retries=10)
    }
)) for rsshub in rsshub_data]

rsshub_multipage_feeders = [root.next(RSSHubMultiPageFeeder(
    url_gen=rsshub['url_gen'], max_pages=rsshub['max_pages'],
    httpx_client_opt_generator=lambda: {
        'timeout': httpx.Timeout(1),
        'transport': httpx.AsyncHTTPTransport(retries=1)
    }
)) for rsshub in rsshub_multipage_data]

branch = Branch()
just_downloaders = [branch.next(JustDownloader(i)) for i in range(1, 4)]
eo_downloaders = [branch.next(EnclosureOnlyDownloader(base_downloader=JustDownloader(i))) for i in range(4, 7)]
ee_downloaders = [branch.next(EnclosureExceptDownloader(base_downloader=JustDownloader(i))) for i in range(7, 10)]

for f in rsshub_feeders:
    f.next(branch)
for f in rsshub_multipage_feeders:
    f.next(branch)

asyncio.run(root(123))
print("sleeping")
time.sleep(10)
