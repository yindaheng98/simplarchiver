import asyncio
import json
import logging
from xml.etree import ElementTree
from typing import Dict

import httpx

from simplarchiver import Feeder


class RSSHubFeeder(Feeder):
    def __init__(self, url: str, logger: logging.Logger = logging.getLogger("RSSHubFeeder")):
        self.__url = url
        self.__logger = logger

    async def get_feeds(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.__url)
            root = ElementTree.XML(response.text)
            fed = set()  # 用集合去除重复项
            for item in root.iter('item'):
                pubDate = item.find('pubDate').text
                link = item.find('link').text
                self.__logger.debug("RSSHubFeeder get an link %s and pubDate %s" % (link, pubDate))
                if link not in fed:
                    fed.add(link)
                    i = {'pubDate': pubDate, 'link': link}
                    if item.find('enclosure') is not None:
                        enclosure = item.find('enclosure').get("url")
                        i['enclosure'] = enclosure
                    self.__logger.info("RSSHubFeeder yield an item: %s" % json.dumps(i))
                    yield i


class TTRSSClient(httpx.AsyncClient):
    sem_list: Dict[str, asyncio.Semaphore] = {}  # 同一时刻一个链接只能有一个客户端登录，这里用一个信号量列表控制

    def __init__(self, url: str, username: str, password: str, **kwargs):
        super().__init__(**kwargs)
        self.__url = url
        self.__username = username
        self.__password = password
        self.__sid = None
        if self.__url not in TTRSSClient.sem_list:  # 给每个链接一个信号量
            TTRSSClient.sem_list[self.__url] = None  # 信号量必须在事件循环开始后生成，此处先给个标记

    async def __aenter__(self):
        for url in TTRSSClient.sem_list:  # 信号量必须在事件循环开始后生成
            if TTRSSClient.sem_list[url] is None:  # 已经生成的信号量不要变
                TTRSSClient.sem_list[url] = asyncio.Semaphore(1)  # 生成信号量
        await TTRSSClient.sem_list[self.__url].__aenter__()  # 同一时刻一个链接只能有一个客户端登录
        await super().__aenter__()
        self.__sid = (await super().post(self.__url, content=json.dumps({
            'op': 'login',
            'user': self.__username,
            'password': self.__password
        }))).json()['content']['session_id']
        return self

    async def __aexit__(self, *args, **kwargs):
        (await super().post(self.__url, content=json.dumps({
            "sid": self.__sid,
            "op": "logout"
        }))).json()
        await super().__aexit__(*args, **kwargs)
        await TTRSSClient.sem_list[self.__url].__aexit__(*args, **kwargs)

    async def api(self, data: dict):
        data['sid'] = self.__sid
        return (await super().post(self.__url, content=json.dumps(data))).json()['content']


class TTRSSFeeder(Feeder):
    def __init__(self, cat_id: int, **kwargs):
        self.__cat_id = cat_id
        self.__client = TTRSSClient(**kwargs)

    async def get_feeds(self):
        async with self.__client as client:
            feeds = await client.api({
                "op": "getFeeds",
                "cat_id": self.__cat_id,
                "limit": None
            })
            for feed in feeds:
                content = await client.api({
                    "op": "getHeadlines",
                    "feed_id": feed['id'],
                    "limit": 1,
                    "view_mode": "all_articles",
                    "order_by": "feed_dates"
                })
                yield {'pubDate': content[0]['link'], 'link': feed['feed_url']}
