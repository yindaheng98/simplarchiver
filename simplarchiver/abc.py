from typing import Callable, Any
from .node import *


class Feeder(Node, metaclass=abc.ABCMeta):
    """Feeder的最基本结构, 可以看作是Chain的Root或Head"""

    @abc.abstractmethod
    async def get_feeds(self):
        yield

    async def call(self, _):
        """
        一个一个地输出item, 其实完全可以由Amplifier替代
        如果不是为了兼容，谁想写这个功能完全没变的class
        """
        try:
            async for i in self.get_feeds():
                yield i
        except Exception:
            self.getLogger().exception("Catch an Exception from your Feeder")


class Amplifier(Node, metaclass=abc.ABCMeta):
    """Amplifier的最基本结构, 输入一个item输出一堆item"""

    @abc.abstractmethod
    async def amplify(self, item):
        yield item

    async def call(self, item):
        """
        由一个item生成一串item
        """
        self.getLogger().debug("amplifying item: %s" % item)
        try:
            async for i in self.amplify(item):
                self.getLogger().debug("item  amplified: %s" % item)
                yield i
        except Exception:
            self.getLogger().exception("Catch an Exception from your Amplifier, skip it: %s" % item)


class Downloader(Node, metaclass=abc.ABCMeta):
    """Downloader的最基本结构, 可以看作是Chain的Tail"""

    @abc.abstractmethod
    async def download(self, item):
        pass

    async def call(self, item):
        """
        等下载完了返回下载结果
        """
        self.getLogger().debug("Download start: %s" % item)
        try:
            yield {
                "item": item,
                "return_code": await self.download(item)
            }
        except Exception:
            self.getLogger().exception("Catch an Exception from your Downloader, skip it: %s" % item)


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
        try:
            self.getLogger().debug("before filter: %s" % item)
            yield await self.filter(item)  # 如果不是为了兼容，谁想用这种方式返回
            self.getLogger().debug("after  filter: %s" % item)
        except Exception:
            self.getLogger().exception("Catch an Exception from your Filter, skip it: %s" % item)


class Callback(Node, metaclass=abc.ABCMeta):
    """回调器，给Downloader用"""

    @abc.abstractmethod
    async def callback(self, item, return_code):
        """
        回调函数接受两个参数，一个是item，一个是被封装的基本Downloader的返回值
        """
        return return_code

    async def call(self, i):
        """
        如果不是为了兼容，谁想写这个功能完全没变的class
        """
        item, return_code = i["item"], i["return_code"]
        self.getLogger().debug("return %s: %s" % (return_code, item))
        self.getLogger().debug("start  callback")
        try:
            await self.callback(item, return_code)
        except Exception:
            self.getLogger().exception("Catch an Exception from your Callback: %s" % item)
        self.getLogger().debug("finish callback")
        yield return_code  # 调用了回调之后将return_code继续向下一级返回  # 如果不是为了兼容，谁想用这种方式返回


class Sequence(Node):
    def __init__(self, *args: Node):
        super().__init__()
        self.__seq = args

    def setTag(self, tag: str = None):
        super().setTag(tag)
        for n in self.__seq:
            n.setTag(tag)

    async def call(self, item):
        async def _call(item, i: int):
            if item is None:
                return
            if i >= len(self.__seq) - 1:
                async for sub in self.__seq[i].call(item):
                    yield sub
            else:
                async for sub in self.__seq[i].call(item):
                    async for res in _call(sub, i + 1):
                        yield res

        async for sub in _call(item, 0):
            yield sub


class FilterFeeder(Feeder):
    """带过滤功能的Feeder"""

    def __init__(self, base_feeder: Feeder, filter: Filter):
        """从一个基本的Feeder生成带过滤的Feeder"""
        super().__init__()
        self.__seq = Sequence(base_feeder, filter)

    async def get_feeds(self):
        """
        带过滤的Feeder的Feed过程
        如果不是为了兼容，谁想写这个功能完全没变的class
        """
        async for item in self.__seq.call({}):
            yield item


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
        self.__seq = Sequence(filter, base_downloader)

    async def download(self, item):
        """
        带过滤的Downloader的Download过程
        如果不是为了兼容，谁想写这个功能完全没变的class
        """
        async for i in self.__seq.call(item):  # 如果不是为了兼容，谁想用这种方式返回
            return i


class CallbackDownloader(Downloader):
    """具有回调功能的Downloader"""

    def __init__(self, base_downloader: Downloader, callback: Callback):
        """从一个基本的Downloader生成具有回调功能Downloader"""
        super().__init__()
        self.__seq = Sequence(base_downloader, callback)

    async def download(self, item):
        """
        如果不是为了兼容，谁想写这个功能完全没变的class
        """
        async for i in self.__seq.call(item):  # 如果不是为了兼容，谁想用这种方式返回
            return i


'''下面这个抽象类是FilterDownloader和CallbackDownloader的杂交'''


class FilterCallbackDownloader(Downloader):
    """同时具有过滤和回调功能的Downloader"""

    def __init__(self, base_downloader: Downloader, filter: Filter, callback: Callback):
        """从一个基本的Downloader生成具有过滤和回调功能Downloader"""
        super().__init__()
        self.__seq = Sequence(filter, base_downloader, callback)

    async def download(self, item):
        """
        过滤+回调
        如果不是为了兼容，谁想写这个功能完全没变的class
        """
        async for i in self.__seq.call(item):  # 如果不是为了兼容，谁想用这种方式返回
            return i
