import abc
import logging

from simplarchiver import Downloader, FilterCallbackDownloader


class UpdateRW(metaclass=abc.ABCMeta):
    """读写更新标记"""

    @abc.abstractmethod
    async def read(self, item) -> bool:
        """
        将item里的更新标记与已记录的更新标记进行比对
        返回是否更新
        """
        pass

    @abc.abstractmethod
    async def write(self, item) -> bool:
        """
        将item里的更新标记记录下来
        返回是否成功
        """
        pass


class UpdateDownloader(FilterCallbackDownloader):
    """
    将一个普通下载器封装为带更新记录和过滤功能的下载器
    这个下载器会记录所有下载成功的item的更新标签
    只有在接收到的item不在更新标签列表或者更新标签发生变化的时候才会执行下载
    """

    def __init__(self,
                 base_downloader: Downloader,
                 update_rw: UpdateRW,
                 logger: logging.Logger = logging.getLogger("UpdateDownloader")):
        """
        base_downloader是要封装的普通下载器
        update_rw用于指定如何写入和读取更新信息
        """
        super().__init__(base_downloader=base_downloader)
        self.__update_rw = update_rw
        self.__logger = logger

    async def filter(self, item):
        """过滤掉更新列表里已有记录且tag值相同的item"""
        try:
            if await self.__update_rw.read(item):
                self.__logger.info('update filter   | item will be downloaded: %s' % item)
                return item
            else:
                self.__logger.info('update filter   | item will be skipped: %s' % item)
                return None
        except Exception:
            self.__logger.exception('update filter   | An error occured, item will be downloaded: %s' % item)
            return item

    async def callback(self, item, return_code):
        """如果下载成功就刷新更新列表里对应的item的tag值"""
        if return_code is None:
            self.__logger.info('update callback | Download finished , update will be writen: %s' % item)
            try:
                if await self.__update_rw.write(item):
                    self.__logger.info('update callback | Update tag has been writen: %s' % item)
                else:
                    self.__logger.info('update callback | Update tag has not been writen: %s' % item)
            except Exception:
                self.__logger.exception('update callback | An error occured when writing update tag: %s' % item)
        else:
            self.__logger.info(
                'update callback | Downloader exit %s, update will not be writen: %s' % (return_code, item))
