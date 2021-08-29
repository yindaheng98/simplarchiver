import json
import logging
import os
from typing import Any, Tuple, Callable

import aiofiles

from simplarchiver import Downloader, FilterCallbackDownloader


class UpdateList:
    """用于操作下载更新标记的记录文件"""

    def __init__(self, path: str, logger: logging.Logger):
        self.__path = path
        self.__logger = logger

    async def __check(self):
        self.__logger.debug("Check if the update list file exists at %s" % self.__path)
        if not os.path.exists(self.__path):  # 先检查一下文件是否存在
            self.__logger.warning("Update list file not exists at %s" % self.__path)
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


class UpdateDownloader(FilterCallbackDownloader):
    """
    将一个普通下载器封装为带更新记录和过滤功能的下载器
    这个下载器会记录所有下载成功的item的更新标签
    只有在接收到的item不在更新标签列表或者更新标签发生变化的时候才会执行下载
    """

    def __init__(self,
                 base_downloader: Downloader,
                 update_list_path: str,
                 update_list_pair_gen: Callable[[Any], Tuple[str, str]],
                 logger: logging.Logger = logging.getLogger("UpdateDownloader")):
        """
        base_downloader是要封装的普通下载器
        update_list_path是更新记录列表的路径
        update_list_pair_gen是生成更新记录键值对的函数
            输入是item
            输出是（item在更新列表中的ID，item的更新标签）
        """
        super().__init__(base_downloader=base_downloader)
        self.__update_list = UpdateList(update_list_path, logger)
        self.__update_list_pair_gen = update_list_pair_gen
        self.__logger = logger

    async def filter(self, item):
        """过滤掉更新列表里已有记录且tag值相同的item"""
        uid, utag = self.__update_list_pair_gen(item)
        if uid is None or utag is None:
            self.__logger.info('update filter   | Update tag   is None  , item will be downloaded: %s' % item)
            return item
        last_utag = await self.__update_list.get(uid)
        self.__logger.debug('update filter   | This update tag is %s; last update tag is %s' % (utag, last_utag))
        if last_utag != utag:
            self.__logger.info('update filter   | Update tag   updated  , item will be downloaded: %s' % item)
            return item
        else:
            self.__logger.info('update filter   | Update tag not updated, item will be skipped   : %s' % uid)

    async def callback(self, item, return_code):
        """如果下载成功就刷新更新列表里对应的item的tag值"""
        uid, utag = self.__update_list_pair_gen(item)
        if uid is None or utag is None:
            self.__logger.info('update callback | Update tag is None, update will not be writen: %s' % item)
            return
        if return_code is None:
            self.__logger.info('update callback | Download finished , update will be writen    : %s' % item)
            await self.__update_list.put(uid, utag)
        else:
            self.__logger.info(
                'update callback | Downloader exit %s, update will not be writen: %s' % (return_code, item))
