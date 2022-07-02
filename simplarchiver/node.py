import abc
import logging
import asyncio


class Logger:
    """用于记录日志的统一接口"""
    __ID: int = 0
    __TagPadding = 0
    __ClassnamePadding = 0

    def __init__(self):
        self.__tag = "Untagged Class %d" % Logger.__ID
        Logger.__ID += 1

    def getLogger(self):
        self.__update_padding()
        return logging.getLogger(("%%-%ds | %%-%ds" % (Logger.__TagPadding, Logger.__ClassnamePadding)
                                  ) % (self.__tag, self.__class__.__name__))

    def setTag(self, tag):
        if tag is not None:
            self.__tag = tag

    def __update_padding(self):
        Logger.__TagPadding = max(Logger.__TagPadding, len(self.__tag))
        Logger.__ClassnamePadding = max(Logger.__ClassnamePadding, len(self.__class__.__name__))


class Node(Logger, metaclass=abc.ABCMeta):
    """
    Chain上的Node
    内部自带一个队列
    """

    @abc.abstractmethod
    async def call(self, item):
        yield item

    def __init__(self, n: int = 1):
        """n表示该节点的并发数"""
        super().__init__()

        def noop(i):
            self.getLogger().warning("There is no next node here for item %s" % i)
            return i

        self.__next__ = noop
        self.__n = n
        self.__queue = None
        self.__semaphore = None

    def next(self, node):
        self.__next__ = node
        return node

    async def __corr(self):
        async with self.__semaphore:
            item = await self.__queue.get()  # 从队列里取一个任务
            async for i in self.call(item):  # 调用之
                if i is not None:
                    await self.__next__(i)  # 结果输出到下一个
            self.__queue.task_done()  # 调用完了通知一声

    async def __call__(self, item):
        if self.__queue is None:
            self.__queue: asyncio.Queue = asyncio.Queue(self.__n)
        await self.__queue.put(item)  # 调用就是直接入队列
        if self.__semaphore is None:
            self.__semaphore = asyncio.Semaphore(self.__n)
        asyncio.create_task(self.__corr())  # 给每一个成功入队列的item都创建一个任务

    async def join(self):
        await self.__next__.join()  # 先等后面的退出
        if self.__queue is not None:
            await self.__queue.join()  # 再退出自己
