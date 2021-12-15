import json
from typing import Dict, Callable
from xml.etree import ElementTree

import httpx

from simplarchiver import Feeder
from .common import default_httpx_client_opt_generator


class RSSHubFeeder(Feeder):
    """
    从RSSHub中获取Feed
    获取到的是RSSHub返回的每个item中的link标签里的内容和pubDate值
    如果有enclosure还会返回enclosure值
    """

    def __init__(self, url: str, httpx_client_opt_generator: Callable[[], Dict] = default_httpx_client_opt_generator):
        """
        httpx_client_opt_generator是一个函数，返回发起请求所用的httpx.AsyncClient()设置
        httpx.AsyncHTTPTransport不能重复使用，所以每次都得返回新的
        """
        super().__init__()
        self.__url = url
        self.httpx_client_opt_generator = httpx_client_opt_generator

    async def get_feeds(self):
        async with httpx.AsyncClient(**self.httpx_client_opt_generator()) as client:
            self.getLogger().debug("get rss xml from %s" % self.__url)
            response = await client.get(self.__url)
            self.getLogger().debug("got rss xml: %s" % response.text)
            root = ElementTree.XML(response.text)
            fed = set()  # 用集合去除重复项
            for item in root.iter('item'):
                pubDate = item.find('pubDate').text
                link = item.find('link').text
                self.getLogger().debug("got fromrss xml: link %s and pubDate %s" % (link, pubDate))
                if link not in fed:
                    fed.add(link)
                    i = {'pubDate': pubDate, 'link': link}
                    if item.find('enclosure') is not None:
                        enclosure = item.find('enclosure').get("url")
                        i['enclosure'] = enclosure
                    self.getLogger().info("yield item: %s" % json.dumps(i))
                    yield i


class RSSHubMultiPageFeeder(Feeder):
    """
    从多个页面的RSSHub中获取Feed
    获取到的是RSSHub返回的每个item中的link标签里的内容和pubDate值
    如果有enclosure还会返回enclosure值
    """

    def __init__(self, url_gen: Callable[[int], str], max_pages: int = 999,
                 httpx_client_opt_generator: Callable[[], Dict] = default_httpx_client_opt_generator):
        """
        url_gen是输入数字生成url的函数
        max_pages是最多获取多少页
        httpx_client_opt_generator是一个函数，返回发起请求所用的httpx.AsyncClient()设置
        httpx.AsyncHTTPTransport不能重复使用，所以每次都得返回新的
        """
        super().__init__()
        self.__url_gen = url_gen
        self.__max_pages = max_pages
        self.httpx_client_opt_generator = httpx_client_opt_generator
        self.__tag_for_feeder = "Temp Feeder"

    def setTag(self, tag):
        super().setTag(tag)
        self.__tag_for_feeder = tag

    async def get_feeds(self):
        for page in range(0, self.__max_pages):
            url = self.__url_gen(page)
            rf = RSSHubFeeder(url, self.httpx_client_opt_generator)
            rf.setTag(self.__tag_for_feeder)
            self.getLogger().info("got page %d: %s" % (page, url))
            try:
                async for item in rf.get_feeds():
                    yield item
            except Exception:
                self.getLogger().exception("Catch an Exception from Temp Feeder:")
