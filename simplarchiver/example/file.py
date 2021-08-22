import os
import logging
from simplarchiver import Feeder


class FileFeeder(Feeder):
    """扫描文件夹，返回所有文件的路径"""
    def __init__(self, root, logger=logging.getLogger("FileFeeder")):
        self.__root = root
        self.__logger = logger

    async def get_feeds(self):
        for top, dirs, files in os.walk(self.__root, topdown=True):
            self.__logger.debug("scanning   | %s" % top)
            for f in files:
                path = os.path.join(top, f)
                self.__logger.debug("file found | %s" % path)
                yield path


class DirFeeder(Feeder):
    """扫描文件夹，返回所有文件夹的路径"""
    def __init__(self, root, logger=logging.getLogger("DirFeeder")):
        self.__root = root
        self.__logger = logger

    async def get_feeds(self):
        for top, dirs, _ in os.walk(self.__root, topdown=True):
            self.__logger.debug("scanning   | %s" % top)
            for d in dirs:
                path = os.path.join(top, d)
                self.__logger.debug("dir  found | %s" % path)
                yield os.path.join(path)


class WalkFeeder(Feeder):
    """扫描文件夹，返回所有文件和文件夹的路径"""
    def __init__(self, root, logger=logging.getLogger("WalkFeeder")):
        self.__root = root
        self.__logger = logger

    async def get_feeds(self):
        for top, dirs, files in os.walk(self.__root, topdown=True):
            self.__logger.debug("scanning   | %s" % top)
            for f in files:
                path = os.path.join(top, f)
                self.__logger.debug("file found | %s" % path)
                yield path
            for d in dirs:
                path = os.path.join(top, d)
                self.__logger.debug("dir  found | %s" % path)
                yield os.path.join(path)
