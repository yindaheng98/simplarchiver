import abc
import logging


class Feeder(metaclass=abc.ABCMeta):
    """最基本的Feeder"""

    @abc.abstractmethod
    async def get_feeds(self):
        yield


class Downloader(metaclass=abc.ABCMeta):
    """最基本的Downloader"""

    @abc.abstractmethod
    async def download(self, item):
        pass


'''以下抽象类是一些可有可无的扩展功能'''


class FilterFeeder(Feeder):
    """带过滤功能的Feeder"""

    __ID: int = 0

    def __init__(self, base_feeder: Feeder):
        """从一个基本的Feeder生成带过滤的Feeder"""
        self.__base_feeder = base_feeder
        self.__id: int = FilterFeeder.__ID
        self.__logger = logging.getLogger("FilterFeeder %d" % self.__id)
        FilterFeeder.__ID += 1

    @abc.abstractmethod
    async def filter(self, item):
        """
        如果过滤器返回了None，则会被过滤掉，不会被yield
        过滤器内可以修改item
        """
        return item

    async def get_feeds(self):
        """带过滤的Feeder的Feed过程"""
        async for item in self.__base_feeder.get_feeds():
            try:
                self.__logger.debug("filter | before: %s" % item)
                item = await self.filter(item)
                self.__logger.debug("filter |  after: %s" % item)
            except Exception:
                self.__logger.exception("Catch an Exception from your Feeder Filter, skip it: %s" % item)
                item = None
            if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被yield
                yield item
            else:
                self.__logger.debug("filter | item is None, skip")


class FilterDownloader(Downloader):
    """带过滤功能的Downloader"""

    __ID: int = 0

    def __init__(self, base_downloader: Downloader):
        """从一个基本的Downloader生成带过滤的Downloader"""
        self.__base_downloader = base_downloader
        self.__id: int = FilterDownloader.__ID
        self.__logger = logging.getLogger("FilterDownloader %d" % self.__id)
        FilterDownloader.__ID += 1

    @abc.abstractmethod
    async def filter(self, item):
        """
        如果过滤器返回了None，则会被过滤掉，不会被Download
        过滤器内可以修改item
        """
        return item

    async def download(self, item):
        """带过滤的Downloader的Download过程"""
        try:
            self.__logger.debug("filter | before: %s" % item)
            item = await self.filter(item)
            self.__logger.debug("filter |  after: %s" % item)
        except Exception:
            self.__logger.exception("Catch an Exception from your Downloader Filter, skip it: %s" % item)
            item = None
        if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被Download
            return await self.__base_downloader.download(item)
        else:
            self.__logger.debug("filter | item is None, skip")


class CallbackDownloader(Downloader):
    """具有回调功能的Downloader"""

    __ID: int = 0

    def __init__(self, base_downloader: Downloader):
        """从一个基本的Downloader生成具有回调功能Downloader"""
        self.__base_downloader = base_downloader
        self.__id: int = CallbackDownloader.__ID
        self.__logger = logging.getLogger("CallbackDownloader %d" % self.__id)
        CallbackDownloader.__ID += 1

    @abc.abstractmethod
    async def callback(self, item, return_code):
        """
        回调函数接受两个参数，一个是item，一个是被封装的基本Downloader的返回值
        """
        pass

    async def download(self, item):
        return_code = await self.__base_downloader.download(item)
        self.__logger.debug("return_code is: %s" % return_code)
        self.__logger.debug("callback | start")
        try:
            await self.callback(item, return_code)
        except Exception:
            self.__logger.exception("Catch an Exception from your Callback:")
        self.__logger.debug("callback |   end")
        return return_code  # 调用了回调之后将return_code继续向下一级返回


'''下面这个抽象类是FilterDownloader和CallbackDownloader的杂交'''


class FilterCallbackDownloader(Downloader):
    """同时具有过滤和回调功能的Downloader"""

    __ID: int = 0

    def __init__(self, base_downloader: Downloader):
        """从一个基本的Downloader生成具有过滤和回调功能Downloader"""
        self.__base_downloader = base_downloader
        self.__id: int = FilterCallbackDownloader.__ID
        self.__logger = logging.getLogger("FilterCallbackDownloader %d" % self.__id)
        FilterCallbackDownloader.__ID += 1

    @abc.abstractmethod
    async def callback(self, item, return_code):
        """
        回调函数接受两个参数，一个是item，一个是被封装的基本Downloader的返回值
        """
        pass

    @abc.abstractmethod
    async def filter(self, item):
        """
        如果过滤器返回了None，则会被过滤掉，不会被Download
        过滤器内可以修改item
        """
        return item

    async def download(self, item):
        """过滤+回调"""
        try:
            self.__logger.debug("filter | before: %s" % item)
            item = await self.filter(item)
            self.__logger.debug("filter |  after: %s" % item)
        except Exception:
            self.__logger.exception("Catch an Exception from your Filter, skip it: %s" % item)
            item = None
        if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被Download
            return_code = await self.__base_downloader.download(item)
            self.__logger.debug("return_code is: %s" % return_code)
            self.__logger.debug("callback | start")
            try:
                await self.callback(item, return_code)
            except Exception:
                self.__logger.exception("Catch an Exception from your Callback:")
            self.__logger.debug("callback |   end")
            return return_code  # 调用了回调之后将return_code继续向下一级返回
        else:
            self.__logger.debug("filter | item is None, skip")
