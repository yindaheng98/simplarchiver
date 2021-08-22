# simplarchiver

一个简单的可扩展异步下载器框架（Python协程小练习）

针对的问题：定时爬虫
* 我需要使用几种不同的方法获取下载链接
* 我所获取到的下载链接包含很多不同方面的内容，每个下载链接都需要使用几种不同的方法进行下载
* 不同的网站有各自的限制，获取下载链接和下载过程都需要限制并发数
* 我需要以指定的时间间隔执行爬虫过程

我想自定义的东西：
* 获取下载链接的方式
* 下载过程

我想让框架帮我管理哪些东西：
* 限制并发数
* 将下载链接传给下载器
* 出错时自动重试
* 以指定时间间隔运行

## 基本思想

名词解释：

| 名词           | 释义                                                                         |
| -------------- | ---------------------------------------------------------------------------- |
| **Item**       | 每一个Item描述了一个待下载的项目，可以看作是下载链接                         |
| **Feeder**     | Item生产者，定义获取下载链接的过程，产生Item以供下载                         |
| **Downloader** | Item消费者，定义获取下载过程，获取Item并依据其内容执行下载过程               |
| **Pair**       | Feeder和Downloader所组成的集合，表示这些Feeder生产的Item要传给这些Downloader |

系统的基本运行过程：

在每个Pair内，将所有Feeder产生的所有Item交给所有Downloader进行下载
* 不同Feeder所产生的Item一视同仁
* 每个Downloader都会收到相同的Item序列

```
Feeder──┐        ┌──Downloader
Feeder──┼──Pair──┼──Downloader
Feeder──┘        └──Downloader
```

## 基本结构

Item、Feeder、Downloader、Pair具体到代码中是四个类：

| 名词           | 代码中的体现                                                                                        | 使用方法                                                                                                                             |
| -------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Item**       | `simplarchiver.Feeder.get_feeds`函数的迭代输出以及`simplarchiver.Downloader.download`函数的输入参数 | 完全由用户自定义，`simplarchiver`只会将其简单的从Feeder搬运到Downloader，不会对其进行操作                                            |
| **Feeder**     | 一个抽象类`simplarchiver.Feeder`                                                                    | 用户继承此类构造自己的子类，从而自定义如何获取Item                                                                                   |
| **Downloader** | 一个抽象类`simplarchiver.Downloader`                                                                | 用户继承此类构造自己的子类，从而自定义如何下载Item                                                                                   |
| **Pair**       | `simplarchiver.Pair`，其构造函数的包含`simplarchiver.Feeder`和`simplarchiver.Downloader`的列表      | 用户以自己定义的`simplarchiver.Feeder`和`simplarchiver.Downloader`子类列表为输入，调用构造函数构造其实例，调用其协程函数执行下载过程 |

### Feeder抽象类`simplarchiver.Feeder`

`simplarchiver.Feeder`是包含一个异步迭代器函数`get_feeds`的抽象类，其迭代输出一个个的Item。

```python
import abc
class Feeder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def get_feeds(self):
        yield
```

继承此类，实现`get_feeds`函数，就能自定义产生什么样的Item。

例如，一个只会睡觉的[`simplarchiver.example.SleepFeeder`](simplarchiver/example/sleep.py)，睡醒了就返回一个字符串作为Item：

```python
class SleepFeeder(Feeder):
    """一个只会睡觉的Feeder"""
    running: int = 0

    def __init__(self, i=uuid.uuid4(), n=10, seconds=None, rand_max=1):
        """
        i表示Feeder的编号
        n表示总共要返回多少个item
        如果指定了seconds，每次就睡眠seconds秒
        如果没有指定seconds，那就睡眠最大rand_max秒的随机时长
        """
        self.seconds = seconds
        self.rand_max = rand_max
        self.n = n
        self.id = i
        self.log('Initialized: seconds=%s, rand_max=%s, n=%s' % (seconds, rand_max, n))

    def log(self, msg):
        logging.info('SleepFeeder     %s | %s' % (self.id, msg))

    async def get_feeds(self):
        for i in range(0, self.n):
            t = random.random() * self.rand_max if self.seconds is None else self.seconds
            SleepFeeder.running += 1
            self.log('Now there are %d SleepFeeder awaiting including me, I will sleep %f seconds' % (SleepFeeder.running, t))
            item = await asyncio.sleep(delay=t, result='item(i=%s,t=%s)' % (i, t))
            self.log('I have slept %f seconds, time to wake up and return an item %s' % (t, item))
            SleepFeeder.running -= 1
            self.log('I wake up, Now there are %d SleepFeeder awaiting' % SleepFeeder.running)
            yield item

```

更多案例：
* [`RandomFeeder`](simplarchiver/example/random.py)：不sleep，不知疲倦地返回随机数的Feeder
* [`RSSHubFeeder`](simplarchiver/example/rss.py)：从RSSHub中爬取Feed Item。获取到的item是RSSHub返回的每个RSS Item中的link标签里的内容和pubDate值，如果有enclosure还会返回enclosure值
* [`RSSHubMultiPageFeeder`](simplarchiver/example/rss.py)：从多个页面的RSSHub中爬取Feed Item，内容同上
* [`TTRSSCatFeeder`](simplarchiver/example/rss.py)：通过TTRSS API从TTRSS的Category中爬取Feed。返回指定的Category中的所有订阅链接和最新的内容链接

### Downloader抽象类`simplarchiver.Downloader`

`simplarchiver.Downloader`是包含一个以Item为输入的协程函数`download`的抽象类。

```python
import abc
class Downloader(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def download(self, item):
        pass
```

继承此类，实现`download`函数，就能自定义对Item执行什么样的下载过程。

例如，一个只会睡觉的[`simplarchiver.example.SleepDownloader`](simplarchiver/example/sleep.py)，收到Item之后先睡一觉然后起床把Item以字符串的方式输出到命令行：

```python
class SleepDownloader(Downloader):
    """一个只会睡觉的Downloader"""
    running: int = 0

    def __init__(self, i=uuid.uuid4(), seconds=None, rand_max=5):
        """
        i表示Feeder的编号
        如果指定了seconds，每次就睡眠seconds秒
        如果没有指定seconds，那就睡眠最大rand_max秒的随机时长
        """
        self.seconds = seconds
        self.rand_max = rand_max
        self.id = i
        self.log('Initialized: seconds=%s, rand_max=%s' % (seconds, rand_max))

    def log(self, msg):
        logging.info('SleepDownloader %s | %s' % (self.id, msg))

    async def download(self, item):
        self.log('I get an item! %s' % item)
        t = random.random() % self.rand_max if self.seconds is None else self.seconds
        SleepDownloader.running += 1
        self.log('Now there are %d SleepDownloader awaiting including me, I will sleep %f seconds' % (SleepDownloader.running, t))
        item = await asyncio.sleep(delay=t, result=item)
        self.log('I have slept %f seconds for the item %s, time to wake up' % (t, item))
        SleepDownloader.running -= 1
        self.log('I wake up, Now there are %d SleepDownloader awaiting' % SleepDownloader.running)
```

更多案例：
* [`JustDownloader`](simplarchiver/example/just.py)：不sleep，不知疲倦地输出收到的Item的Downloader
* [`SubprocessDownloader`](simplarchiver/example/subprocess.py)：根据Item开子进程执行系统调用的Downloader

### Pair类`simplarchiver.Pair`

`simplarchiver.Pair`包含了整个系统的`simplarchiver`核心逻辑。

```python
class Pair:
    def __init__(self,
                 feeders: List[Feeder] = [],
                 downloaders: List[Downloader] = [],
                 time_delta: timedelta = timedelta(minutes=30),
                 feeder_concurrency: int = 3,
                 downloader_concurrency: int = 3):
        ...
    ...
    async def coroutine_once(self):
        ...
    async def coroutine_forever(self):
        ...
```

其中，构造函数输入为：

| 形参                     | 含义                                                                           |
| ------------------------ | ------------------------------------------------------------------------------ |
| `feeders`                | 由`simplarchiver.Feeder`构成的列表，用户在此处输入自己定义的Feeder             |
| `downloaders`            | 由`simplarchiver.Downloader`构成的列表，用户在此处输入自己定义的Downloader     |
| `time_delta`             | 在`coroutine_forever`函数中当一轮下载全部完成后，sleep多长时间再开始下一轮下载 |
| `feeder_concurrency`     | 同一时刻最多可以并发运行多少个`simplarchiver.Feeder.get_feeds().__anext__()`   |
| `downloader_concurrency` | 同一时刻最多可以并发运行多少个`simplarchiver.Downloader.download()`            |

两个主要协程的运行过程为：

`coroutine_once`，运行一次：
1. 为`downloaders`里的Downloader创建下载队列，启动所有Downloader等待下载
2. 启动`feeders`里的所有Feeder获取要下载的items
3. 对于Feeder输出的每个item，在每个Downloader下载队列里面都push一个
4. Feeder输出结束之后向每个Downloader下载队列发送`None`作为停止信号
5. Downloader运行完所有的下载任务后收到最后的停止信号就退出
6. 等待所有Downloader退出

`coroutine_forever`，永久运行：
1. 运行`coroutine_once`协程并等待其完成
2. 如果`coroutine_once`抛出了错误，则忽略错误并立即回到步骤1
3. 如果`coroutine_once`正常退出，则等待`time_delta`时长后再回到步骤1

除了构造函数之外，协程开始前还可以使用这些方法修改设置：

```python
class Pair:
    ...
    def add_feeder(self, feeder: Feeder):
        ...

    def add_feeders(self, feeders: List[Feeder]):
        ...

    def add_downloader(self, downloader: Downloader):
        ...

    def add_downloaders(self, downloaders: List[Downloader]):
        ...

    def set_timedelta(self, timedelta: timedelta):
        ...

    def set_feeder_concurrency(self, n: int):
        ...

    def set_downloader_concurrency(self, n: int):
        ...
    ...
```

例如，使用上面定义的`SleepFeeder`和`SleepDownloader`构造一个包含4个Feeder和4个Downloader、以5秒为间隔运行的、Feeder和Downloader并发数分别为3和4的`simplarchiver.Pair`（位于[test_Sleep.py](test_Sleep.py)）：：

```python
from simplarchiver import Pair
from simplarchiver.example import SleepFeeder, SleepDownloader
from datetime import timedelta

pair = Pair([SleepFeeder(0)], [SleepDownloader(0)], timedelta(seconds=5), 3, 4)
for i in range(1, 4):
    pair.add_feeder(SleepFeeder(i))
for i in range(1, 4):
    pair.add_downloader(SleepDownloader(i))
```

要启动运行，只需要使用`asyncio.run`运行`simplarchiver.Pair`的协程即可（位于[test_Sleep.py](test_Sleep.py)）：

```python
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log(msg):
    logging.info('test_Pair | %s' % msg)

log("pair.coroutine_once()")
asyncio.run(pair.coroutine_once()) # 运行一次
log("pair.coroutine_forever()")
asyncio.run(pair.coroutine_forever()) # 永远运行
```

## 扩展：`simplarchiver.Controller`

进一步的需求：并行运行多个`simplarchiver.Pair`
* 在好几个项目里面都用到了这个框架，现在有一堆`simplarchiver.Pair`需要运行
* 不想给每个`simplarchiver.Pair`都弄一个进程，想把它们放在一个事件循环里运行，节约资源

实现：so easy，用`asyncio.gather`运行多个`simplarchiver.Pair.coroutine_forever()`就好了，这个过程封装为[`simplarchiver.Controller`](simplarchiver/controller.py)：

```python
from .pair import *
from typing import List


class Controller:
    def __init__(self, pairs: List[Pair] = []):
        """
        feeder-downloader对列表，键为id值为Pair
        每个Pair都是独立运行的
        """
        self.__pairs = []
        self.add_pairs(pairs)

    async def coroutine(self):
        await asyncio.gather(*[pair.coroutine_forever() for pair in self.__pairs])
```

并发运行Pair轻而易举：
```python
from simplarchiver import Controller, Pair
from simplarchiver.example import RandomFeeder, JustDownloader

controller = Controller()
for i in range(1, 4):
    controller.add_pair(
        Pair([RandomFeeder('(%d,%d)' % (i, j)) for j in range(1, 4)],
             [JustDownloader('(%d,%d)' % (i, j)) for j in range(1, 4)],
             timedelta(seconds=i * 5), i, i))
asyncio.run(controller.coroutine())
```