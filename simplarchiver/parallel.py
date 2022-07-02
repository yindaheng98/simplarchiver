import asyncio
from .abc import *


class ParallelNode(Node, metaclass=abc.ABCMeta):
    """以指定数量进行并发调用的Node"""

    def __init__(self, n: int = 1):
        super().__init__()
        self.__corn = n
        self.__running = False
        self.__queue = asyncio.Queue(n)

    def __start(self):
        if self.__running:  # 如果已经在运行
            return  # 就不运行
        self.__running = True  # 运行标记
        for i in range(1, self.__corn + 1):  # 创建指定数量的执行进程
            asyncio.create_task(self.__coroutine(i))

    async def __coroutine(self, i: int):
        log = lambda s: self.getLogger().debug('coroutine %d | %s' % (i, s))
        log("start")
        while True:
            self.getLogger().debug('coroutine | wait for next item')
            item = await self.__queue.get()
            self.getLogger().debug('coroutine | item got: %s' % item)
            if item is None:
                self.__queue.task_done()
                break  # 用None表示feed结束
            async with self.__semaphore:
                self.getLogger().debug('coroutine | download process start: %s' % item)
                try:
                    await self.__downloader.download(item)
                except Exception:
                    self.getLogger().exception('Catch an Exception from your Downloader:')
                self.getLogger().debug('coroutine | download process exited: %s' % item)
                self.__queue.task_done()  # task_done配合join可以判断任务是否全部完成
        self.getLogger().debug('coroutine | end')

    async def __call__(self, item):
        if not self.__running:
            self.__running = True
            asyncio.create_task(self.__coroutine())
        async for i in self.call(item):
            if i is not None:
                async with self.__semaphore:
                    await self.__next__(i)
