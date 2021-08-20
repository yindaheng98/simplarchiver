import asyncio
import logging
from typing import Callable, Any, Awaitable

from simplarchiver import Downloader


class SubprocessDownloader(Downloader):
    """运行指令开子进程下载"""

    def __init__(self, cmd_gen: Callable[[dict], str],
                 callback: Callable[[Any, str, int], Awaitable] = None,
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
        self.__callback = callback if callback is not None else self.__default_callback
        self.__logger = logger

    async def __default_callback(self, item, cmd, returncode):
        self.__logger.debug('SubprocessDownloader subprocess exit: %s' % {
            'item': item, 'cmd': cmd, 'returncode': returncode
        })

    async def __readline_info(self, f):
        async for line in f:
            self.__logger.info(
                'SubprocessDownloader subprocess stdout: %s' % line.decode(self.__stdout_encoding).strip())

    async def __readline_debug(self, f):
        async for line in f:
            self.__logger.debug(
                'SubprocessDownloader subprocess stderr: %s' % line.decode(self.__stdout_encoding).strip())

    async def download(self, item):
        self.__logger.debug("SubprocessDownloader get an item: %s" % item)
        cmd = self.__cmd_gen(item)
        self.__logger.info("SubprocessDownloader run cmd: %s" % cmd)
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        await asyncio.gather(self.__readline_info(proc.stdout), self.__readline_debug(proc.stderr))
        await self.__callback(item, cmd, await proc.wait())
