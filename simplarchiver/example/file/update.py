import json
import abc
import os
from typing import Any, Tuple, Callable

import aiofiles

from simplarchiver import Downloader, UpdateRW, UpdateDownloader, Logger


class UpdatePG(Logger, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def get(self, key: str) -> Any:
        pass

    @abc.abstractmethod
    async def put(self, key: str, update_tag: str):
        pass


class UpdateList(UpdatePG):
    """用于操作下载更新标记的记录文件"""

    def __init__(self, path: str):
        super().__init__()
        self.__path = path

    async def __check(self):
        self.getLogger().debug("Check if the update list file exists at %s" % self.__path)
        try:
            async with aiofiles.open(self.__path, 'r', encoding='utf8') as f:
                json.loads(await f.read())  # 先检查一下文件是否可以读取
        except Exception as e:
            self.getLogger().error("Update list file has error %s" % e)
            async with aiofiles.open(self.__path, 'w', encoding='utf8') as f:
                await f.write(json.dumps({}))  # 不存在的话就先写个空列表进去
                self.getLogger().warning("A new empty update list file generated to %s" % self.__path)

    async def get(self, key: str) -> Any:
        """读取更新标记"""
        await self.__check()
        async with aiofiles.open(self.__path, 'r', encoding='utf8') as f:
            ulist = json.loads(await f.read())
            self.getLogger().debug("Searching update tag %s in update list %s" % (key, self.__path))
            if key in ulist:
                value = ulist[key]
                self.getLogger().debug("Update tag %s found in update list %s, it is %s" % (key, self.__path, value))
                return value
            else:
                self.getLogger().debug("Update tag %s not found in update list %s" % (key, self.__path))
                return None

    async def put(self, key: str, update_tag: str):
        """写入更新标记"""
        await self.__check()
        async with aiofiles.open(self.__path, 'r+', encoding='utf8') as f:
            self.getLogger().debug(
                "Put the update tag %s with the value %s into the update list %s" % (key, update_tag, self.__path))
            ulist = json.loads(await f.read())
            ulist[key] = update_tag
            await f.seek(0)
            await f.truncate()
            await f.write(json.dumps(ulist, indent=4))


class UpdateDir(UpdatePG):
    """用于操作下载更新标记的记录文件"""

    def __init__(self, path: str):
        super().__init__()
        self.__path = path

    async def get(self, key: str) -> Any:
        path = os.path.join(self.__path, key)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)  # 啥都不管先创建文件夹
            if not os.path.isfile(path):  # 先检查一下文件是否存在
                self.getLogger().warning("Update list file not exist in %s" % path)
                async with aiofiles.open(path, 'w', encoding='utf8') as f:
                    await f.write('')  # 不存在的话就先创建
                    self.getLogger().warning("A new empty update list file generated to %s" % self.__path)
                    return ''
            async with aiofiles.open(path, 'r', encoding='utf8') as f:
                value = await f.read()
                return value
        except Exception as e:
            self.getLogger().error("Update list file has error when get %s" % e)
            return ''

    async def put(self, key: str, update_tag: str):
        try:
            path = os.path.join(self.__path, key)
            os.makedirs(os.path.dirname(path), exist_ok=True)  # 啥都不管先创建文件夹
            async with aiofiles.open(path, 'w', encoding='utf8') as f:
                await f.write(update_tag)  # 直接写文件
                self.getLogger().warning("A new empty update list file generated to %s" % self.__path)
        except Exception as e:
            self.getLogger().error("Update list file has error when put %s" % e)


class UpdatePGRW(UpdateRW):
    def __init__(self, update_put_get: UpdatePG, update_list_pair_gen: Callable[[Any], Tuple[str, str]]):
        super().__init__()
        self.__update_put_get = update_put_get
        self.__update_list_pair_gen = update_list_pair_gen

    def setTag(self, tag: str = None):
        super().setTag(tag)
        self.__update_put_get.setTag(tag)

    async def read(self, item) -> bool:
        """过滤掉更新列表里已有记录且tag值相同的item"""
        uid, utag = self.__update_list_pair_gen(item)
        if uid is None or utag is None:
            self.getLogger().info('read | Update tag is None, return True: %s' % uid)
            return True
        last_utag = await self.__update_put_get.get(uid)
        self.getLogger().debug('read | This update tag is %s; last update tag is %s' % (utag, last_utag))
        if last_utag != utag:
            self.getLogger().info('read | Update tag updated, return True: %s' % uid)
            return True
        else:
            self.getLogger().info('read | Update tag not updated, return False: %s' % uid)
            return False

    async def write(self, item) -> bool:
        """如果下载成功就刷新更新列表里对应的item的tag值"""
        uid, utag = self.__update_list_pair_gen(item)
        await self.__update_put_get.put(uid, utag)
        return True


def CentralizedUpdateDownloader(
        base_downloader: Downloader,
        update_list_path: str,
        update_list_pair_gen: Callable[[Any], Tuple[str, str]]):
    f = UpdateDownloader(
        base_downloader,
        UpdatePGRW(UpdateList(update_list_path), update_list_pair_gen)
    )
    f.setTag('CentralizedUpdateDownloader')
    return f


def DecentralizedUpdateDownloader(
        base_downloader: Downloader,
        update_list_path: str,
        update_list_pair_gen: Callable[[Any], Tuple[str, str]]):
    f = UpdateDownloader(
        base_downloader,
        UpdatePGRW(UpdateDir(update_list_path), update_list_pair_gen)
    )
    f.setTag('CentralizedUpdateDownloader')
    return f
