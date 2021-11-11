import os

from simplarchiver import Feeder, Filter, FilterFeeder


class FileFeeder(Feeder):
    """扫描文件夹，返回所有文件的路径"""

    def __init__(self, root):
        super().__init__()
        self.__root = root

    async def get_feeds(self):
        for top, dirs, files in os.walk(self.__root, topdown=True):
            self.getLogger().debug("scanning   | %s" % top)
            for f in files:
                path = os.path.join(top, f)
                self.getLogger().debug("file found | %s" % path)
                yield path


class DirFeeder(Feeder):
    """扫描文件夹，返回所有文件夹的路径"""

    def __init__(self, root):
        super().__init__()
        self.__root = root

    async def get_feeds(self):
        for top, dirs, _ in os.walk(self.__root, topdown=True):
            self.getLogger().debug("scanning   | %s" % top)
            for d in dirs:
                path = os.path.join(top, d)
                self.getLogger().debug("dir  found | %s" % path)
                yield os.path.join(path)


class WalkFeeder(Feeder):
    """扫描文件夹，返回所有文件和文件夹的路径"""

    def __init__(self, root):
        super().__init__()
        self.__root = root

    async def get_feeds(self):
        for top, dirs, files in os.walk(self.__root, topdown=True):
            self.getLogger().debug("scanning   | %s" % top)
            for f in files:
                path = os.path.join(top, f)
                self.getLogger().debug("file found | %s" % path)
                yield path
            for d in dirs:
                path = os.path.join(top, d)
                self.getLogger().debug("dir  found | %s" % path)
                yield os.path.join(path)


class ExtFilter(Filter):
    """筛选指定文件后缀名的文件"""

    def __init__(self, extension: str):
        super().__init__()
        self.__extension = extension.lower()

    async def filter(self, item):
        self.getLogger().debug("item       | %s" % item)
        ext = os.path.splitext(item)[1].lower()
        if self.__extension == ext:
            self.getLogger().debug("extension  | %s = %s" % (ext, self.__extension))
            return item
        else:
            self.getLogger().debug("extension  | %s ≠ %s" % (ext, self.__extension))
            return None


def ExtFilterFeeder(base_feeder: FileFeeder, extension: str):
    f = FilterFeeder(base_feeder, ExtFilter(extension))
    f.setTag('ExtFilterFeeder')
    return f
