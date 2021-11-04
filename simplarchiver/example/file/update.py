import abc
import json
import logging
from typing import Any, Tuple, Callable

import aiofiles

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


class UpdateList:
    """用于操作下载更新标记的记录文件"""

    def __init__(self, path: str, logger: logging.Logger):
        self.__path = path
        self.__logger = logger

    async def __check(self):
        self.__logger.debug("Check if the update list file exists at %s" % self.__path)
        try:
            async with aiofiles.open(self.__path, 'r', encoding='utf8') as f:
                json.loads(await f.read())  # 先检查一下文件是否可以读取
        except Exception as e:
            self.__logger.error("Update list file has error %s" % e)
            async with aiofiles.open(self.__path, 'w', encoding='utf8') as f:
                await f.write(json.dumps({}))  # 不存在的话就先写个空列表进去
                self.__logger.warning("A new empty update list file generated to %s" % self.__path)

    async def get(self, key: str) -> Any:
        """读取更新标记"""
        await self.__check()
        async with aiofiles.open(self.__path, 'r', encoding='utf8') as f:
            ulist = json.loads(await f.read())
            self.__logger.debug("Searching update tag %s in update list %s" % (key, self.__path))
            if key in ulist:
                value = ulist[key]
                self.__logger.debug("Update tag %s found in update list %s, it is %s" % (key, self.__path, value))
                return value
            else:
                self.__logger.debug("Update tag %s not found in update list %s" % (key, self.__path))
                return None

    async def put(self, key: str, update_tag: str):
        """写入更新标记"""
        await self.__check()
        async with aiofiles.open(self.__path, 'r+', encoding='utf8') as f:
            self.__logger.debug(
                "Put the update tag %s with the value %s into the update list %s" % (key, update_tag, self.__path))
            ulist = json.loads(await f.read())
            ulist[key] = update_tag
            await f.seek(0)
            await f.truncate()
            await f.write(json.dumps(ulist, indent=4))


class UpdateListRW(UpdateRW):
    def __init__(self,
                 update_list_path: str,
                 update_list_pair_gen: Callable[[Any], Tuple[str, str]],
                 logger: logging.Logger = logging.getLogger("UpdateDownloader")):
        self.__update_list = UpdateList(update_list_path, logger)
        self.__update_list_pair_gen = update_list_pair_gen
        self.__logger = logger

    async def read(self, item) -> bool:
        """过滤掉更新列表里已有记录且tag值相同的item"""
        uid, utag = self.__update_list_pair_gen(item)
        if uid is None or utag is None:
            self.__logger.info('read | Update tag is None, return True: %s' % uid)
            return True
        last_utag = await self.__update_list.get(uid)
        self.__logger.debug('read | This update tag is %s; last update tag is %s' % (utag, last_utag))
        if last_utag != utag:
            self.__logger.info('read | Update tag updated, return True: %s' % uid)
            return True
        else:
            self.__logger.info('read | Update tag not updated, return False: %s' % uid)
            return False

    async def write(self, item) -> bool:
        """如果下载成功就刷新更新列表里对应的item的tag值"""
        uid, utag = self.__update_list_pair_gen(item)
        await self.__update_list.put(uid, utag)
        return True


def CentralizedUpdateDownloader(
        base_downloader: Downloader,
        update_list_path: str,
        update_list_pair_gen: Callable[[Any], Tuple[str, str]],
        logger: logging.Logger = logging.getLogger("UpdateDownloader")):
    return UpdateDownloader(
        base_downloader,
        UpdateListRW(update_list_path, update_list_pair_gen, logger),
        logger
    )
