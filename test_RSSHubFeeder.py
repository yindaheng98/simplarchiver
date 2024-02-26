import asyncio
import logging
import time

import httpx

from simplarchiver import Pair, ForestRoot, Branch
from simplarchiver.example import JustDownloader
from simplarchiver.example.rss import EnclosureOnlyDownloader, EnclosureExceptDownloader
from simplarchiver.example.rss import RSSHubFeeder, RSSHubMultiPageFeeder
from test_secret import rsshub_data, url_gen

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s | %(levelname)-8s | %(name)-26s | %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)


root = ForestRoot()
rsshub_feeders = [root.next(RSSHubFeeder(
    url=rsshub,
    httpx_client_opt_generator=lambda: {
        'timeout': httpx.Timeout(20.0),
        'transport': httpx.AsyncHTTPTransport(retries=10)
    }
)) for rsshub in rsshub_data]

rsshub_multipage_feeders = [root.next(RSSHubMultiPageFeeder(
    url_gen=url_gen, max_pages=10,
    httpx_client_opt_generator=lambda: {
        'timeout': httpx.Timeout(1),
        'transport': httpx.AsyncHTTPTransport(retries=1)
    }
))]

branch = Branch()
just_downloaders = [branch.next(JustDownloader(i)) for i in range(1, 4)]
eo_downloaders = [branch.next(EnclosureOnlyDownloader(base_downloader=JustDownloader(i))) for i in range(4, 7)]
ee_downloaders = [branch.next(EnclosureExceptDownloader(base_downloader=JustDownloader(i))) for i in range(7, 10)]

for f in rsshub_feeders:
    f.next(branch)
for f in rsshub_multipage_feeders:
    f.next(branch)
root.setTag("RSSHub Feeder")

async def main():
    await root(123)
    await root.join()
asyncio.run(main())
print("sleeping")
time.sleep(10)
