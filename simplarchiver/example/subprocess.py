import asyncio
import logging
from typing import Callable

from simplarchiver import Downloader


class SubprocessDownloader(Downloader):
    """运行指令开子进程下载"""

    def __init__(self, cmd_gen: Callable[[dict], str],
                 stdout_encoding='utf-8',
                 logger: logging.Logger = logging.getLogger("SubprocessDownloader")):
        """
        url_gen是输入item生成指令的函数
        stdout_encoding是标准输出的解码方式
        callback是指令运行完成后的回调函数，其输入分别是：
            1) 收到的item
            2) 生成的指令
            3) 程序退出时返回的returncode
        """
        self.__cmd_gen = cmd_gen
        self.__stdout_encoding = stdout_encoding
        self.__logger = logger

    async def __readline_info(self, f):
        async for line in f:
            self.__logger.info(
                'stdout  | %s' % line.decode(self.__stdout_encoding).strip())

    async def __readline_debug(self, f):
        async for line in f:
            self.__logger.info(
                'stderr  | %s' % line.decode(self.__stdout_encoding).strip())

    async def download(self, item):
        self.__logger.debug("item    | %s" % item)
        cmd = self.__cmd_gen(item)
        self.__logger.info("command | %s" % cmd)
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        await asyncio.gather(self.__readline_info(proc.stdout), self.__readline_debug(proc.stderr))
        return_code = await proc.wait()
        return None if return_code <= 0 else return_code  # 返回return code
