import asyncio
import json
import logging
from xml.etree import ElementTree
from typing import Dict, Callable

import httpx

from simplarchiver import Feeder, FilterFeeder, FilterDownloader, Downloader


def default_httpx_client_opt_generator():
    return {
        'timeout': httpx.Timeout(10.0),
        'transport': httpx.AsyncHTTPTransport(retries=5)
    }


class RSSHubFeeder(Feeder):
    """
    从RSSHub中获取Feed
    获取到的是RSSHub返回的每个item中的link标签里的内容和pubDate值
    如果有enclosure还会返回enclosure值
    """

    def __init__(self, url: str, logger: logging.Logger = logging.getLogger("RSSHubFeeder"),
                 httpx_client_opt_generator: Callable[[], Dict] = default_httpx_client_opt_generator):
        """
        httpx_client_opt_generator是一个函数，返回发起请求所用的httpx.AsyncClient()设置
        httpx.AsyncHTTPTransport不能重复使用，所以每次都得返回新的
        """
        self.__url = url
        self.__logger = logger
        self.httpx_client_opt_generator = httpx_client_opt_generator

    async def get_feeds(self):
        async with httpx.AsyncClient(**self.httpx_client_opt_generator()) as client:
            self.__logger.debug("get rss xml from %s" % self.__url)
            response = await client.get(self.__url)
            self.__logger.debug("got rss xml: %s" % response.text)
            root = ElementTree.XML(response.text)
            fed = set()  # 用集合去除重复项
            for item in root.iter('item'):
                pubDate = item.find('pubDate').text
                link = item.find('link').text
                self.__logger.debug("got fromrss xml: link %s and pubDate %s" % (link, pubDate))
                if link not in fed:
                    fed.add(link)
                    i = {'pubDate': pubDate, 'link': link}
                    if item.find('enclosure') is not None:
                        enclosure = item.find('enclosure').get("url")
                        i['enclosure'] = enclosure
                    self.__logger.info("yield item: %s" % json.dumps(i))
                    yield i


class RSSHubMultiPageFeeder(Feeder):
    """
    从多个页面的RSSHub中获取Feed
    获取到的是RSSHub返回的每个item中的link标签里的内容和pubDate值
    如果有enclosure还会返回enclosure值
    """

    def __init__(self, url_gen: Callable[[int], str], max_pages: int = 999,
                 logger: logging.Logger = logging.getLogger("RSSHubMultiPageFeeder"),
                 httpx_client_opt_generator: Callable[[], Dict] = default_httpx_client_opt_generator):
        """
        url_gen是输入数字生成url的函数
        max_pages是最多获取多少页
        httpx_client_opt_generator是一个函数，返回发起请求所用的httpx.AsyncClient()设置
        httpx.AsyncHTTPTransport不能重复使用，所以每次都得返回新的
        """
        self.__url_gen = url_gen
        self.__max_pages = max_pages
        self.__logger = logger
        self.httpx_client_opt_generator = httpx_client_opt_generator

    async def get_feeds(self):
        for page in range(0, self.__max_pages):
            url = self.__url_gen(page)
            rf = RSSHubFeeder(url, self.__logger)
            rf.httpx_client_opt = self.httpx_client_opt_generator
            self.__logger.info("got page %d: %s" % (page, url))
            rfn = 0  # 计数
            async for item in rf.get_feeds():
                rfn += 1
                yield item
            if rfn <= 0:
                return  # 计数，如果一个item都没有返回说明是最后一页，可以退出


class TTRSSClient(httpx.AsyncClient):
    """一个简单的异步TTRSS客户端"""
    sem_list: Dict[str, asyncio.Semaphore] = {}  # 同一时刻一个链接只能有一个客户端登录，这里用一个信号量列表控制

    def __init__(self, url: str, username: str, password: str,
                 logger: logging.Logger = logging.getLogger("TTRSSClient"),
                 **kwargs):
        super().__init__(**kwargs)
        self.__url = url
        self.__username = username
        self.__password = password
        self.__logger = logger
        self.__sid = None
        if self.__url not in TTRSSClient.sem_list:  # 给每个链接一个信号量
            TTRSSClient.sem_list[self.__url] = None  # 信号量必须在事件循环开始后生成，此处先给个标记

    async def __aenter__(self):
        for url in TTRSSClient.sem_list:  # 信号量必须在事件循环开始后生成
            if TTRSSClient.sem_list[url] is None:  # 已经生成的信号量不要变
                self.__logger.debug('semaphore for TTRSS API %s initialized' % url)
                TTRSSClient.sem_list[url] = asyncio.Semaphore(1)  # 生成信号量
        await TTRSSClient.sem_list[self.__url].__aenter__()  # 同一时刻一个链接只能有一个客户端登录
        self.__logger.debug('semaphore for TTRSS API %s got' % self.__url)
        await super().__aenter__()
        self.__logger.debug('httpx cli for TTRSS API %s initialized' % self.__url)
        self.__sid = (await super().post(self.__url, content=json.dumps({
            'op': 'login',
            'user': self.__username,
            'password': self.__password
        }))).json()['content']['session_id']
        self.__logger.info('TTRSS API login successful, sid: %s' % self.__sid)
        return self

    async def __aexit__(self, *args, **kwargs):
        (await super().post(self.__url, content=json.dumps({
            "sid": self.__sid,
            "op": "logout"
        }))).json()
        await super().__aexit__(*args, **kwargs)
        self.__logger.info('TTRSS API logout successful, sid: %s' % self.__sid)
        await TTRSSClient.sem_list[self.__url].__aexit__(*args, **kwargs)
        self.__logger.debug('semaphore for TTRSS API %s released' % self.__url)

    async def api(self, data: dict):
        data['sid'] = self.__sid
        self.__logger.debug("post data to  TTRSS API %s: %s" % (self.__url, data))
        return (await super().post(self.__url, content=json.dumps(data))).json()['content']


class TTRSSCatFeeder(Feeder):
    """
    从TTRSS的Category中获取Feed
    返回指定的Category中的所有订阅链接和最新的内容链接
    """

    def __init__(self, url: str, username: str, password: str, cat_id: int,
                 logger: logging.Logger = logging.getLogger("TTRSSFeeder"),
                 httpx_client_opt_generator: Callable[[], Dict] = default_httpx_client_opt_generator):
        """
        httpx_client_opt_generator是一个函数，返回发起请求所用的httpx.AsyncClient()设置
        httpx.AsyncHTTPTransport不能重复使用，所以每次都得返回新的
        """
        self.ttrss_client_opt = {
            'url': url, 'username': username, 'password': password,
            'logger': logger
        }  # 发起请求所用的ttrss客户端设置
        self.__cat_id = cat_id
        self.__logger = logger
        self.httpx_client_opt_generator = httpx_client_opt_generator

    async def get_feeds(self):
        async with TTRSSClient(**self.httpx_client_opt_generator(), **self.ttrss_client_opt) as client:
            self.__logger.info("succeeded login to TTRSS")
            feeds = await client.api({
                "op": "getFeeds",
                "cat_id": self.__cat_id,
                "limit": None
            })
            self.__logger.debug("got cat data of cat %d: %s" % (self.__cat_id, json.dumps(feeds)))
            for feed in feeds:
                content = await client.api({
                    "op": "getHeadlines",
                    "feed_id": feed['id'],
                    "limit": 1,
                    "view_mode": "all_articles",
                    "order_by": "feed_dates"
                })
                i = {'recent': content[0]['link'], 'link': feed['feed_url']}
                self.__logger.info("yield an item: %s" % json.dumps(i))
                yield i


class TTRSSHubLinkFeeder(FilterFeeder):
    """
    从TTRSS返回的Category Feed中获取原始link
    实际上就是在filter中根据TTRSS返回的item["link"]获取RSS Feed里面的link标签内容，以此替换item["link"]
    """

    def __init__(self, base_feeder: TTRSSCatFeeder, logger: logging.Logger = logging.getLogger("TTRSSHubLinkFeeder"),
                 httpx_client_opt_generator: Callable[[], Dict] = default_httpx_client_opt_generator):
        """
        httpx_client_opt_generator是一个函数，返回发起请求所用的httpx.AsyncClient()设置
        httpx.AsyncHTTPTransport不能重复使用，所以每次都得返回新的
        """
        super().__init__(base_feeder)
        self.__logger = logger
        self.httpx_client_opt_generator = httpx_client_opt_generator

    async def filter(self, item):
        rss_link = item["link"]
        async with httpx.AsyncClient(**self.httpx_client_opt_generator()) as client:
            response = await client.get(rss_link)
            root = ElementTree.XML(response.content)
            channel = root.find('channel')
            link = channel.find('link').text
            item["link"] = link
            item['pubDate'] = list(root.iter('item'))[0].find('pubDate').text
        self.__logger.info("got the original link of %s: %s" % (rss_link, item["link"]))
        return item


class EnclosureOnlyDownloader(FilterDownloader):
    """筛掉没有Enclosure的，只要有Enclosure的"""

    def __init__(self, base_downloader: Downloader,
                 logger: logging.Logger = logging.getLogger("EnclosureOnlyDownloader")):
        super().__init__(base_downloader)
        self.__logger = logger

    async def filter(self, item):
        if 'enclosure' in item:
            self.__logger.info("This item has an enclosure, keep it: %s" % item)
            return item
        else:
            self.__logger.info("This item has no enclosure, drop it: %s" % item)
            return None


class EnclosureExceptDownloader(FilterDownloader):
    """筛掉有Enclosure的，只要没有Enclosure的"""

    def __init__(self, base_downloader: Downloader,
                 logger: logging.Logger = logging.getLogger("EnclosureExceptDownloader")):
        super().__init__(base_downloader)
        self.__logger = logger

    async def filter(self, item):
        if 'enclosure' in item:
            self.__logger.info("This item has an enclosure, drop it: %s" % item)
            return None
        else:
            self.__logger.info("This item has no enclosure, keep it: %s" % item)
            return item
