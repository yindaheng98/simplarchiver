from .abc import *


class UpdateRW(Logger, metaclass=abc.ABCMeta):
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


class UpdateFilter(Filter):

    def __init__(self, update_rw: UpdateRW):
        """
        base_downloader是要封装的普通下载器
        update_rw用于指定如何写入和读取更新信息
        """
        super().__init__()
        # update_rw.setTag(tag) # 继承自内置类Filter的类不需要在初始化时setTag
        self.__update_rw = update_rw

    def setTag(self, tag: str = None):  # 继承自内置类Filter的类的Tag是在FilterFeeder或FilterDownloader初始化时setTag进去的
        super().setTag(tag)
        self.__update_rw.setTag(tag)

    async def filter(self, item):
        """过滤掉更新列表里已有记录且tag值相同的item"""
        try:
            if await self.__update_rw.read(item):
                self.getLogger().info('item will be downloaded: %s' % item)
                return item
            else:
                self.getLogger().info('item will be skipped: %s' % item)
                return None
        except Exception:
            self.getLogger().exception('An error occured, item will be downloaded: %s' % item)
            return item


class UpdeteCallback(Callback):

    def __init__(self, update_rw: UpdateRW):
        """
        base_downloader是要封装的普通下载器
        update_rw用于指定如何写入和读取更新信息
        """
        super().__init__()
        # update_rw.setTag(tag) # 继承自内置类Filter的类不需要在初始化时setTag
        self.__update_rw = update_rw

    def setTag(self, tag: str = None):  # 继承自内置类Filter的类的Tag是在FilterFeeder或FilterDownloader初始化时setTag进去的
        super().setTag(tag)
        self.__update_rw.setTag(tag)

    async def callback(self, item, return_code):
        """如果下载成功就刷新更新列表里对应的item的tag值"""
        if return_code is None:
            self.getLogger().info('Download finished , update will be writen: %s' % item)
            try:
                if await self.__update_rw.write(item):
                    self.getLogger().info('Update tag has been writen: %s' % item)
                else:
                    self.getLogger().info('Update tag has not been writen: %s' % item)
            except Exception:
                self.getLogger().exception('An error occured when writing update tag: %s' % item)
        else:
            self.getLogger().info('Downloader exit %s, update will not be writen: %s' % (return_code, item))


def UpdateDownloader(base_downloader: Downloader, update_rw: UpdateRW):
    f = FilterCallbackDownloader(base_downloader, UpdateFilter(update_rw), UpdeteCallback(update_rw))
    f.setTag('UpdateDownloader')
    return f
