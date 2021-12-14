import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Callable

import httpx

from simplarchiver import Feeder
from .common import default_httpx_client_opt_generator


class TTRSSGenFeeder(Feeder):
    """
    从TTRSS的GeneratedFeeds链接中获取Feed
    获取到的是TTRSS返回的每个entry中的link标签里的内容和pubDate值
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
            self.getLogger().debug("get GeneratedFeeds json from %s" % self.__url)
            response = await client.get(self.__url)
            data = json.loads(response.text)
            self.getLogger().debug("got GeneratedFeeds json: %s" % data)
            for article in data['articles']:
                article['pubDate'] = 'Invalid'
                if 'updated' in article:
                    pubDate = datetime.strptime(article['updated'], "%Y-%m-%dT%H:%M:%S%z")
                    article['pubDate'] = datetime.strftime(pubDate, "%a, %d %b %Y %H:%M:%S GMT")
                yield article


class TTRSSClient(httpx.AsyncClient):
    """一个简单的异步TTRSS客户端"""
    sem_list: Dict[str, asyncio.Semaphore] = {}  # 同一时刻一个链接只能有一个客户端登录，这里用一个信号量列表控制

    def __init__(self, url: str, username: str, password: str, **kwargs):
        super().__init__(**kwargs)
        self.__url = url
        self.__username = username
        self.__password = password
        self.__logger = logging.getLogger("TTRSSClient")
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
        try:
            data = (await super().post(self.__url, content=json.dumps({
                'op': 'login',
                'user': self.__username,
                'password': self.__password
            }))).json()
            self.__logger.debug('TTRSS API login response: %s' % data)
            self.__sid = data['content']['session_id']
            self.__logger.debug('TTRSS API login successful, sid: %s' % self.__sid)
        except Exception:
            self.__logger.exception('TTRSS API login failed, error: ')
        return self

    async def __aexit__(self, *args, **kwargs):
        try:
            data = (await super().post(self.__url, content=json.dumps({
                "sid": self.__sid,
                "op": "logout"
            }))).json()
            self.__logger.debug('TTRSS API logout response: %s' % data)
            self.__logger.debug('TTRSS API logout successful, sid: %s' % self.__sid)
        except Exception:
            self.__logger.exception('TTRSS API logout failed, error: ')
        await super().__aexit__(*args, **kwargs)
        await TTRSSClient.sem_list[self.__url].__aexit__(*args, **kwargs)
        self.__logger.debug('semaphore for TTRSS API %s released' % self.__url)

    async def api(self, data: dict):
        data['sid'] = self.__sid
        self.__logger.debug("post data to  TTRSS API %s: %s" % (self.__url, data))
        try:
            return (await super().post(self.__url, content=json.dumps(data))).json()['content']
        except Exception:
            self.__logger.exception('TTRSS API post failed, error: ')
            return None


class TTRSSCatFeeder(Feeder):
    """
    从TTRSS的Category中获取Feed
    返回指定的Category中的所有订阅链接和最新的内容链接
    """

    def __init__(self, url: str, username: str, password: str, cat_id: int,
                 httpx_client_opt_generator: Callable[[], Dict] = default_httpx_client_opt_generator):
        """
        httpx_client_opt_generator是一个函数，返回发起请求所用的httpx.AsyncClient()设置
        httpx.AsyncHTTPTransport不能重复使用，所以每次都得返回新的
        """
        super().__init__()
        self.ttrss_client_opt = {
            'url': url, 'username': username, 'password': password
        }  # 发起请求所用的ttrss客户端设置
        self.__cat_id = cat_id
        self.httpx_client_opt_generator = httpx_client_opt_generator

    async def get_feeds(self):
        async with TTRSSClient(**self.httpx_client_opt_generator(), **self.ttrss_client_opt) as client:
            self.getLogger().info("succeeded login to TTRSS")
            feeds = await client.api({
                "op": "getFeeds",
                "cat_id": self.__cat_id,
                "limit": None
            })
            self.getLogger().debug("got cat data of cat %d: %s" % (self.__cat_id, json.dumps(feeds)))
            for feed in feeds:
                content = await client.api({
                    "op": "getHeadlines",
                    "feed_id": feed['id'],
                    "limit": 1,
                    "view_mode": "all_articles",
                    "order_by": "feed_dates"
                })
                i = {'recent_link': content[0]['link'], 'feed_url': feed['feed_url']}
                self.getLogger().info("yield an item: %s" % json.dumps(i))
                yield i
