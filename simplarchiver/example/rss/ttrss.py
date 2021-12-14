import json
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
                yield article
