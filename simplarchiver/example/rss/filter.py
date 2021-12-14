from typing import Dict, Callable
from xml.etree import ElementTree

import httpx

from simplarchiver import Feeder, Filter, FilterFeeder, FilterDownloader, Downloader
from .common import default_httpx_client_opt_generator


class TTRSSHubLinkFilter(Filter):
    """
    从TTRSS返回的Category Feed中获取原始link
    实际上就是在filter中根据TTRSS返回的item["link"]获取RSS Feed里面的link标签内容，以此替换item["link"]
    """

    def __init__(self, httpx_client_opt_generator: Callable[[], Dict] = default_httpx_client_opt_generator):
        """
        httpx_client_opt_generator是一个函数，返回发起请求所用的httpx.AsyncClient()设置
        httpx.AsyncHTTPTransport不能重复使用，所以每次都得返回新的
        """
        super().__init__()
        self.httpx_client_opt_generator = httpx_client_opt_generator

    async def filter(self, item):
        """
        从TTRSS返回的Category Feed中获取原始link
        实际上就是根据TTRSS返回的item["link"]获取RSS Feed里面的link标签内容，以此替换item["link"]
        专为TTRSSHubLinkFeeder和TTRSSHubLinkDownloader设计
        """
        feed_url = item["feed_url"]
        self.getLogger().info("getting the original link of %s" % feed_url)
        async with httpx.AsyncClient(**self.httpx_client_opt_generator()) as client:
            response = await client.get(feed_url)
            root = ElementTree.XML(response.content)
            channel = root.find('channel')
            link = channel.find('link').text
            item["link"] = link
            item['pubDate'] = list(root.iter('item'))[0].find('pubDate').text
        self.getLogger().info("got the original link of %s: %s" % (feed_url, item["link"]))
        return item


def TTRSSHubLinkFeeder(base_feeder: Feeder,
                       httpx_client_opt_generator: Callable[[], Dict] = default_httpx_client_opt_generator):
    f = FilterFeeder(base_feeder, TTRSSHubLinkFilter(httpx_client_opt_generator))
    f.setTag('TTRSSHubLinkFeeder')
    return f


def TTRSSHubLinkDownloader(base_downloader: Downloader,
                           httpx_client_opt_generator: Callable[[], Dict] = default_httpx_client_opt_generator):
    f = FilterDownloader(base_downloader, TTRSSHubLinkFilter(httpx_client_opt_generator))
    f.setTag('TTRSSHubLinkDownloader')
    return f


class EnclosureOnlyFilter(Filter):
    """筛掉没有Enclosure的，只要有Enclosure的"""

    async def filter(self, item):
        if 'enclosure' in item:
            self.getLogger().info("This item has an enclosure, keep it: %s" % item)
            return item
        else:
            self.getLogger().info("This item has no enclosure, drop it: %s" % item)
            return None


def EnclosureOnlyDownloader(base_downloader: Downloader):
    f = FilterDownloader(base_downloader, EnclosureOnlyFilter())
    f.setTag('EnclosureOnlyDownloader')
    return f


class EnclosureExceptFilter(Filter):
    """筛掉有Enclosure的，只要没有Enclosure的"""

    async def filter(self, item):
        if 'enclosure' in item:
            self.getLogger().info("This item has an enclosure, drop it: %s" % item)
            return None
        else:
            self.getLogger().info("This item has no enclosure, keep it: %s" % item)
            return item


def EnclosureExceptDownloader(base_downloader: Downloader):
    f = FilterDownloader(base_downloader, EnclosureOnlyFilter())
    f.setTag('EnclosureExceptDownloader')
    return f
