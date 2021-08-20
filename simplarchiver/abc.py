import abc


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

    def __init__(self, base_feeder: Feeder):
        """从一个基本的Feeder生成带过滤的Feeder"""
        self.__base_feeder = base_feeder

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
            item = await self.filter(item)
            if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被yield
                yield item


class FilterDownloader(Downloader):
    """带过滤功能的Downloader"""

    def __init__(self, base_downloader: Downloader):
        """从一个基本的Downloader生成带过滤的Downloader"""
        self.__base_downloader = base_downloader

    @abc.abstractmethod
    async def filter(self, item):
        """
        如果过滤器返回了None，则会被过滤掉，不会被Download
        过滤器内可以修改item
        """
        return item

    async def download(self, item):
        """带过滤的Downloader的Download过程"""
        item = await self.filter(item)
        if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被Download
            return await self.__base_downloader.download(item)


class CallbackDownloader(Downloader):
    """具有回调功能的Downloader"""

    def __init__(self, base_downloader: Downloader):
        """从一个基本的Downloader生成具有回调功能Downloader"""
        self.__base_downloader = base_downloader

    @abc.abstractmethod
    async def callback(self, item, return_code):
        """
        回调函数接受两个参数，一个是item，一个是被封装的基本Downloader的返回值
        """
        pass

    async def download(self, item):
        return await self.callback(item, await self.__base_downloader.download(item))


'''下面这个抽象类是FilterDownloader和CallbackDownloader的杂交'''


class FilterCallbackDownloader(Downloader):
    """同时具有过滤和回调功能的Downloader"""

    def __init__(self, base_downloader: Downloader):
        """从一个基本的Downloader生成具有过滤和回调功能Downloader"""
        self.__base_downloader = base_downloader

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
        item = await self.filter(item)
        if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被Download
            return_code = await self.__base_downloader.download(item)
            await self.callback(item, return_code)
            return return_code  # 调用了回调之后将return_code继续向下一级返回
