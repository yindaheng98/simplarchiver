import json
import logging
from xml.etree import ElementTree

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
