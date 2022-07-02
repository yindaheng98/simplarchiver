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

        class Noop(Logger):
            async def __call__(self, item):
                self.getLogger().warning("There is no next node here for item %s" % item)
                return item

            async def join(self):
                return

        self.__next__: Node = Noop()
        self.__n = n
        self.__queue = None
        self.__semaphore = None

    def next(self, node):
        self.__next__: Node = node
        return node

    async def __corr(self):
        async with self.__semaphore:
            item = await self.__queue.get()  # 从队列里取一个任务
            async for i in self.call(item):  # 调用之
                if i is not None:
                    await self.__next__(i)  # 结果输出到下一个
            self.__queue.task_done()  # 调用完了通知一声

    async def __call__(self, item):
        if item is None:  # 过滤掉None
            return
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


class Branch(Node):
    """有分支的Node, 将输入的item复制给各分支"""

    def call(self, item):
        return item

    def __init__(self):
        super().__init__()
        self.__next__ = []

    def next(self, node: Node):
        self.__next__.append(node)
        return self

    async def __call__(self, item):
        if item is None:  # 过滤掉None
            return
        i = self.call(item)
        if i is not None:
            await asyncio.gather(*[n(i) for n in self.__next__])  # 必须等这个item成功输入到所有分支上才算完成

    async def join(self):
        await asyncio.gather(*[n.join() for n in self.__next__])  # 要等后面的全部退出


class Root(Node):

    def call(self, item):
        return item

    def __init__(self):
        super().__init__()

    async def __call__(self, item):
        await self.__next__(item)
        await self.__next__.join()


class MultiRoot(Branch):

    def __init__(self):
        super().__init__()

    async def __call__(self, item):
        await super().__call__(item)
        await super().join()
