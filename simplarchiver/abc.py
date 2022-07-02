import abc
import logging
from typing import Callable, Any


class Logger:
    """用于记录日志的统一接口"""
    __ID: int = 0
    __TagPadding = 0
    __ClassnamePadding = 0

    def __init__(self):
        self.__tag = "Untagged Class %d" % Logger.__ID
        Logger.__ID += 1

    def getLogger(self):
        self.__update_padding()
        return logging.getLogger(("%%-%ds | %%-%ds" % (Logger.__TagPadding, Logger.__ClassnamePadding)
                                  ) % (self.__tag, self.__class__.__name__))

    def setTag(self, tag):
        if tag is not None:
            self.__tag = tag

    def __update_padding(self):
        Logger.__TagPadding = max(Logger.__TagPadding, len(self.__tag))
        Logger.__ClassnamePadding = max(Logger.__ClassnamePadding, len(self.__class__.__name__))


class Node(Logger, metaclass=abc.ABCMeta):
    """Chain上的Node"""

    @abc.abstractmethod
    async def call(self, item):
        yield

    def __init__(self):
        super().__init__()
        self.n = None

    def next(self, node):
        self.n = node

    async def __call__(self, item):
        async for i in self.call(item):
            if i is not None and self.n is not None:
                self.n(i)


class Feeder(Node, metaclass=abc.ABCMeta):
    """Feeder的最基本结构, 可以看作是Chain的Root或Head"""

    @abc.abstractmethod
    async def get_feeds(self):
        yield

    async def call(self, item):
        """
        一个一个地输出item
        如果不是为了兼容，谁想写这个功能完全没变的class
        """
        async for i in self.get_feeds():
            yield i


class Downloader(Node, metaclass=abc.ABCMeta):
    """Downloader的最基本结构, 可以看作是Chain的Tail"""

    @abc.abstractmethod
    async def download(self, item):
        pass

    async def call(self, item):
        """
        等下载完了返回下载结果
        """
        yield await self.download(item)


'''以下抽象类是一些可有可无的扩展功能'''


class Filter(Node, metaclass=abc.ABCMeta):
    """过滤器，给FilterFeeder和FilterDownloader用"""

    @abc.abstractmethod
    async def filter(self, item):
        """
        如果过滤器返回了None，则会被过滤掉，不会被yield
        过滤器内可以修改item
        """
        return item

    async def call(self, item):
        """
        如果不是为了兼容，谁想写这个功能完全没变的class
        """
        yield await self.filter(item)


class FilterFeeder(Feeder):
    """带过滤功能的Feeder"""

    def __init__(self, base_feeder: Feeder, filter: Filter):
        """从一个基本的Feeder生成带过滤的Feeder"""
        super().__init__()
        self.__base_feeder = base_feeder
        self.__filter = filter

    def setTag(self, tag: str = None):
        super().setTag(tag)
        self.__base_feeder.setTag(tag)
        self.__filter.setTag(tag)

    async def get_feeds(self):
        """带过滤的Feeder的Feed过程"""
        async for item in self.__base_feeder.get_feeds():
            item_t = item
            try:
                self.getLogger().debug("before filter: %s" % item)
                item = await self.__filter.filter(item)
                self.getLogger().debug("after  filter: %s" % item)
            except Exception:
                self.getLogger().exception("Catch an Exception from your Feeder Filter, skip it: %s" % item)
                item = None
            if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被yield
                self.getLogger().info("feed: %s" % item)
                yield item
            else:
                self.getLogger().info("skip: %s" % item_t)


class AmplifierFeeder(Feeder):
    """基于一个Feeder生成的item生成多个Feeder进而生成多个item"""

    def __init__(self, base_feeder: Feeder, ampl_feeder_gen: Callable[[Any], Feeder]):
        """从一个基本的Feeder和一个放大器Feeder生成器生成带过滤的Feeder"""
        super().__init__()
        self.__base_feeder = base_feeder
        self.__ampl_feeder_gen = ampl_feeder_gen
        self.__ampl_tag = None

    def setTag(self, tag: str = None):
        super().setTag(tag)
        self.__base_feeder.setTag(tag)
        self.__ampl_tag = tag

    async def get_feeds(self):
        async for item in self.__base_feeder.get_feeds():  # 获取基本Feeder里的item
            try:
                self.getLogger().debug("amplifying item: %s" % item)
                sub_feeder = self.__ampl_feeder_gen(item)  # 生成放大器Feeder
                sub_feeder.setTag(self.__ampl_tag)
                self.getLogger().debug("item  amplified: %s" % item)
            except Exception:
                self.getLogger().exception("Catch an Exception from your Amplifier Generator, skip it: %s" % item)
                sub_feeder = None
            if sub_feeder is not None:
                try:
                    async for sub_item in sub_feeder.get_feeds():  # 获取放大器Feeder里的item
                        self.getLogger().info("ampl: %s" % sub_item)
                        yield sub_item
                except Exception:
                    self.getLogger().exception("Catch an Exception from your Amplifier Feeder, skip it: %s" % item)
            else:
                self.getLogger().debug("Amplifier Feeder is None, skip")


class FilterDownloader(Downloader):
    """带过滤功能的Downloader"""

    def __init__(self, base_downloader: Downloader, filter: Filter):
        """从一个基本的Downloader生成带过滤的Downloader"""
        super().__init__()
        self.__base_downloader = base_downloader
        self.__filter = filter

    def setTag(self, tag: str = None):
        super().setTag(tag)
        self.__base_downloader.setTag(tag)
        self.__filter.setTag(tag)

    async def download(self, item):
        """带过滤的Downloader的Download过程"""
        item_t = item
        try:
            self.getLogger().debug("before filter: %s" % item)
            item = await self.__filter.filter(item)
            self.getLogger().debug("after  filter: %s" % item)
        except Exception:
            self.getLogger().exception("Catch an Exception from your Downloader Filter, skip it: %s" % item)
            item = None
        if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被Download
            self.getLogger().info("keep: %s" % item)
            return await self.__base_downloader.download(item)
        else:
            self.getLogger().info("skip: %s" % item_t)


class Callback(Logger, metaclass=abc.ABCMeta):
    """回调器，给CallbackDownloader用"""

    @abc.abstractmethod
    async def callback(self, item, return_code):
        """
        回调函数接受两个参数，一个是item，一个是被封装的基本Downloader的返回值
        """
        pass


class CallbackDownloader(Downloader):
    """具有回调功能的Downloader"""

    def __init__(self, base_downloader: Downloader, callback: Callback):
        """从一个基本的Downloader生成具有回调功能Downloader"""
        super().__init__()
        self.__base_downloader = base_downloader
        self.__callback = callback

    def setTag(self, tag: str = None):
        super().setTag(tag)
        self.__base_downloader.setTag(tag)
        self.__callback.setTag(tag)

    async def download(self, item):
        return_code = await self.__base_downloader.download(item)
        self.getLogger().debug("return %s: %s" % (return_code, item))
        self.getLogger().debug("start  callback")
        try:
            await self.__callback.callback(item, return_code)
        except Exception:
            self.getLogger().exception("Catch an Exception from your Callback: %s" % item)
        self.getLogger().debug("finish callback")
        return return_code  # 调用了回调之后将return_code继续向下一级返回


'''下面这个抽象类是FilterDownloader和CallbackDownloader的杂交'''


class FilterCallbackDownloader(Downloader):
    """同时具有过滤和回调功能的Downloader"""

    def __init__(self, base_downloader: Downloader, filter: Filter, callback: Callback):
        """从一个基本的Downloader生成具有过滤和回调功能Downloader"""
        super().__init__()
        self.__base_downloader = base_downloader
        self.__filter = filter
        self.__callback = callback

    def setTag(self, tag: str = None):
        super().setTag(tag)
        self.__base_downloader.setTag(tag)
        self.__filter.setTag(tag)
        self.__callback.setTag(tag)

    async def download(self, item):
        """过滤+回调"""
        item_t = item
        try:
            self.getLogger().debug("before filter: %s" % item)
            item = await self.__filter.filter(item)
            self.getLogger().debug("after  filter: %s" % item)
        except Exception:
            self.getLogger().exception("Catch an Exception from your Filter, skip it: %s" % item)
            item = None
        if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被Download
            self.getLogger().info("keep: %s" % item)
            return_code = await self.__base_downloader.download(item)
            self.getLogger().debug("return_code is: %s" % return_code)
            self.getLogger().debug("start  callback")
            try:
                await self.__callback.callback(item, return_code)
            except Exception:
                self.getLogger().exception("Catch an Exception from your Callback:")
            self.getLogger().debug("finish callback")
            return return_code  # 调用了回调之后将return_code继续向下一级返回
        else:
            self.getLogger().info("skip: %s" % item_t)
