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
* [`simplarchiver.example.RandomFeeder`](simplarchiver/example/random.py)：不sleep，不知疲倦地返回随机数的Feeder
* [`simplarchiver.example.RSSHubFeeder`](simplarchiver/example/rss.py)：从RSSHub中爬取Feed Item。获取到的item是RSSHub返回的每个RSS Item中的link标签里的内容和pubDate值，如果有enclosure还会返回enclosure值
* [`simplarchiver.example.RSSHubMultiPageFeeder`](simplarchiver/example/rss.py)：从多个页面的RSSHub中爬取Feed Item，内容同上
* [`simplarchiver.example.TTRSSCatFeeder`](simplarchiver/example/rss.py)：通过TTRSS API从TTRSS的Category中爬取Feed。返回指定的Category中的所有订阅链接和最新的内容链接

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
* [`simplarchiver.example.JustDownloader`](simplarchiver/example/just.py)：不sleep，不知疲倦地输出收到的Item的Downloader
* [`simplarchiver.example.SubprocessDownloader`](simplarchiver/example/subprocess.py)：根据Item开子进程执行系统调用的Downloader

### Pair类`simplarchiver.Pair`

`simplarchiver.Pair`包含了整个系统的`simplarchiver`核心逻辑。

```python
class Pair:
    def __init__(self,
                 feeders: List[Feeder] = [],
                 downloaders: List[Downloader] = [],
                 start_deny: timedelta = timedelta(seconds=4),
                 interval: timedelta = timedelta(minutes=30),
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
| `start_deny`             | sleep多长时间后启动第一轮下载 |
| `interval`               | 在`coroutine_forever`函数中当一轮下载全部完成后，sleep多长时间再开始下一轮下载 |
| `feeder_concurrency`     | `feeders`所输入的`Feeder`最多可以同时运行多少个   |
| `downloader_concurrency` | `downloaders`所输入的`Downloader`最多可以同时运行多少个            |

注意：一个`Downloader`实例的`simplarchiver.Downloader.download()`不会被并行调用，所以如果设置了`downloader_concurrency`大于`downloaders`列表的长度，同一时刻最多也只会有`len(downloaders)`个`simplarchiver.Downloader.download()`并行调用，每个`Downloader`实例最多有一个`simplarchiver.Downloader.download()`在运行

TODO：未来可能会改变`downloader_concurrency`的实现方式，让一个`Downloader`实例可以并行运行多个`simplarchiver.Downloader.download()`过程，使`downloader_concurrency`控制同一时刻最多可以并发运行多少个`simplarchiver.Downloader.download()`

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
3. 如果`coroutine_once`正常退出，则等待`interval`时长后再回到步骤1

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

pair = Pair([SleepFeeder(0)], [SleepDownloader(0)], timedelta(seconds=1), timedelta(seconds=5), 3, 4)
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

实现：用`asyncio.gather`运行多个`simplarchiver.Pair.coroutine_forever()`就好了，这个过程封装为[`simplarchiver.Controller`](simplarchiver/controller.py)：

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
             timedelta(seconds=i * 1), timedelta(seconds=i * 5), i, i))
asyncio.run(controller.coroutine())
```

## 扩展：过滤

进一步的需求：
* 有些Item，我想处理或筛选一下再传给Downloader去下载
* 有些Item的处理我想放在Feeder输出之后，让修改和筛选传给到所有的Downloader
* 有些Item的处理我想放在Downloader输入之前，让修改和筛选只传给一个Downloader

### 实现Feeder的Item后处理：Feed过滤器[`simplarchiver.FilterFeeder`](simplarchiver/abc.py)

* 一个带有过滤函数`filter`的抽象类
* 继承自`simplarchiver.Feeder`
* 内部存储一个`simplarchiver.Feeder`作为基础Feeder
* 在其`get_feeds`中先调用基础Feeder的`get_feeds`，再调用`filter`过滤之

```python
class FilterFeeder(Feeder):
    """带过滤功能的Feeder"""

    def __init__(self, base_feeder: Feeder):
        """从一个基本的Feeder生成带过滤的Feeder"""
        self.__base_feeder = base_feeder

    @abc.abstractmethod
    async def filter(self, item):
        """
        如果过滤器返回了None，则会被过滤掉，不会被yield
        过滤器内可以修改item
        """
        return item

    async def get_feeds(self):
        """带过滤的Feeder的Feed过程"""
        async for item in self.__base_feeder.get_feeds():
            item = await self.filter(item)
            if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被yield
                yield item
```

于是，用户可以继承此类，定义自己的过滤方案，然后在构造时将需要过滤的Feeder封装进去即可。例如，一个随机删除一半Item的Feed过滤器[`simplarchiver.example.RandomFilterFeeder`](simplarchiver/example/random.py)：

```python
class RandomFilterFeeder(FilterFeeder):
    """一个随机过滤item的Feeder"""

    def __init__(self, base_feeder: Feeder,
                 logger: logging.Logger = logging.getLogger("RandomFilterFeeder")):
        super().__init__(base_feeder)
        self.__logger = logger

    async def filter(self, item):
        r = random.random()
        self.__logger.info(
            "RandomFilterFeeder rand  a number %f and item %s, " % (r, item) + (
                "keep the item" if r > 0.5 else "drop the item"))
        return item if r > 0.5 else None
```

在构造时将要过滤的Feeder封装进去即可：
```python
pair = Pair([
    RandomFilterFeeder(
        SleepFeeder(0)
    )
], [SleepDownloader(0)], timedelta(seconds=1), timedelta(seconds=5), 4, 4)
```

因为Feed过滤器也是继承自`simplarchiver.Feeder`，所以它天生就是可以嵌套的。例如我要随机删除某个Feeder四分之三的输出Item，那就嵌套一下：
```python
pair = Pair([
    RandomFilterFeeder(
        RandomFilterFeeder(
            SleepFeeder(0)
        )
    )
], [SleepDownloader(0)], timedelta(seconds=1), timedelta(seconds=5), 4, 4)
```

更多案例：
* [`simplarchiver.example.TTRSSHubLinkFeeder`](simplarchiver/example/rss.py)：用于封装`simplarchiver.example.TTRSSCatFeeder`，`TTRSSCatFeeder`返回的`item['link']`字段是RSS订阅链接，`TTRSSHubLinkFeeder.filter`将根据此RSS订阅链接获取原网页地址替换到`item['link']`中。

### 实现Downloader的Item预处理：Download过滤器[`simplarchiver.FilterDownloader`](simplarchiver/abc.py)

和[`simplarchiver.FilterFeeder`](simplarchiver/abc.py)类似，只不过`simplarchiver.FilterFeeder`的`filter`函数在`get_feeds`的`yield`之后调用，`simplarchiver.FilterDownloader`的`filter`函数在`download`之前调用：

```python
class FilterDownloader(Downloader):
    """带过滤功能的Downloader"""

    def __init__(self, base_downloader: Downloader):
        """从一个基本的Downloader生成带过滤的Downloader"""
        self.__base_downloader = base_downloader

    @abc.abstractmethod
    async def filter(self, item):
        """
        如果过滤器返回了None，则会被过滤掉，不会被Download
        过滤器内可以修改item
        """
        return item

    async def download(self, item):
        """带过滤的Downloader的Download过程"""
        item = await self.filter(item)
        if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被Download
            return await self.__base_downloader.download(item)
```

于是，用户可以继承此类，定义自己的过滤方案，然后在构造时将需要过滤的Downloader封装进去即可。例如，一个随机删除一半Item的Download过滤器[`simplarchiver.example.RandomFilterDownloader`](simplarchiver/example/random.py)：

```python
class RandomFilterDownloader(FilterDownloader):
    """一个随机过滤item的Downloader"""

    def __init__(self, base_downloader: Downloader,
                 logger: logging.Logger = logging.getLogger("RandomFilterDownloader")):
        super().__init__(base_downloader)
        self.__logger = logger

    async def filter(self, item):
        r = random.random()
        self.__logger.info(
            "RandomFilterDownloader rand a number %f and item %s, " % (r, item) + (
                "keep the item" if r > 0.5 else "drop the item"))
        return item if r > 0.5 else None
```

在构造时将要过滤的Downloader封装进去即可：
```python
pair = Pair([SleepFeeder(0)], [
    RandomFilterDownloader(
        SleepDownloader(0)
    )
], timedelta(seconds=1), timedelta(seconds=5), 4, 4)
```

同样，Download过滤器也是可以嵌套的。和上面的Feed过滤器的嵌套案例一样，我要让某个Downloader随机跳过四分之三的输入Item，那就嵌套一下：
```python
pair = Pair([SleepFeeder(0)], [
    RandomFilterDownloader(
        RandomFilterDownloader(
            SleepDownloader(0)
        )
    )
], timedelta(seconds=1), timedelta(seconds=5), 4, 4)
```

更多案例：
* [`simplarchiver.example.EnclosureOnlyDownloader`](simplarchiver/example/rss.py)：筛选出包含`enclosure`字段的Item
* [`simplarchiver.example.EnclosureExceptDownloader`](simplarchiver/example/rss.py)：筛选出不包含`enclosure`字段的Item

## 扩展：放大

首先明确“放大”的概念：
* 有些Feeder输出的item可用作为其他Feeder生成时的输入
* 一个item放进另一个Feeder里会得到多个item
* 对于一个Feeder输出的每个item，都可以放进另一个Feeder里生成多个item
* 于是，item变多了，就叫做“放大”

以RSS订阅为例，要获取所有的订阅详情，需要使用[`simplarchiver.example.TTRSSCatFeeder`](simplarchiver/example/rss.py)从TTRSS上获取所有RSS订阅的链接，再使用[`simplarchiver.example.RSSHubFeeder`](simplarchiver/example/rss.py)访问这些RSS订阅链接，从中读取所有的RSS item。

TTRSS上的订阅链接是`simplarchiver.example.TTRSSCatFeeder`的输出，也是`simplarchiver.example.RSSHubFeeder`的输入；`simplarchiver.example.RSSHubFeeder`对于每个订阅链接都生成多个订阅项。

基于这个需求，可以构造如下的Feeder放大器类：
```python
class AmplifierFeeder(Feeder):
    """基于一个Feeder生成的item生成多个Feeder进而生成多个item"""

    def __init__(self, base_feeder: Feeder, ampl_feeder_gen: Callable[[Any], Feeder]):
        """从一个基本的Feeder和一个放大器Feeder生成器生成带过滤的Feeder"""
        self.__base_feeder = base_feeder
        self.__ampl_feeder_gen = ampl_feeder_gen

    async def get_feeds(self):
        async for item in self.__base_feeder.get_feeds():  # 获取基本Feeder里的item
            sub_feeder = self.__ampl_feeder_gen(item)  # 生成放大器Feeder
            if sub_feeder is not None:
                async for sub_item in sub_feeder.get_feeds():  # 获取放大器Feeder里的item
                    yield sub_item
```
很简单，就是输入一个基本Feeder和一个放大器Feeder生成函数，对基本Feeder输出的每个item都调用放大器Feeder生成函数生成放大器Feeder，再从放大器Feeder里读item。

## 扩展：Download回调

进一步的需求：

* 一个`Downloader.download`退出了，我想看看是下载完成了还是下载失败了
* 在下载完成后，我还想根据下载完成或是失败的信息进行进一步的操作
* 我定义了好几个不同的Downloader，它们的返回信息都差不多，进一步的操作的差不多，我不想在每个`Downloader.download`末尾都写一遍一样的代码

实现：回调机制

* 一个带有回调函数`callback`的抽象类
* 继承自`simplarchiver.Downloader`
* 内部存储一个`simplarchiver.Downloader`作为基础Downloader
* 在其`download`中先调用基础Feeder的`download`，再将其返回值和Item作为`callback`的输入

```python
class CallbackDownloader(Downloader):
    """具有回调功能的Downloader"""

    def __init__(self, base_downloader: Downloader):
        """从一个基本的Downloader生成具有回调功能Downloader"""
        self.__base_downloader = base_downloader

    @abc.abstractmethod
    async def callback(self, item, return_code):
        """
        回调函数接受两个参数，一个是item，一个是被封装的基本Downloader的返回值
        """
        pass

    async def download(self, item):
        return await self.callback(item, await self.__base_downloader.download(item))
```

于是，用户可以继承此类，定义自己的回调，然后在构造时将需要回调的Downloader封装进去即可。例如，一个输出`download`函数返回值的回调[`simplarchiver.example.JustLogCallbackDownloader`](simplarchiver/example/just.py)：

```python
class JustLogCallbackDownloader(CallbackDownloader):
    """只是把Callback的内容输出到log而已"""

    def __init__(self, base_downloader: Downloader,
                 logger: logging.Logger = logging.getLogger("JustLogCallbackDownloader")):
        super(JustLogCallbackDownloader, self).__init__(base_downloader)
        self.__logger = logger

    async def callback(self, item, return_code):
        self.__logger.info(
            "JustLogCallbackDownloader run its callback, return_code: %s, item: %s" % (return_code, item))
```

在构造时将要过滤的Downloader封装进去即可：
```python
pair = Pair([SleepFeeder(0)], [
    JustLogCallbackDownloader(
        SleepDownloader(0)
    )
], timedelta(seconds=1), timedelta(seconds=5), 4, 4)
```

Download回调自然也是可以嵌套的：
```python
pair = Pair([SleepFeeder(0)], [
    JustLogCallbackDownloader(
        JustLogCallbackDownloader(
            SleepDownloader(0)
        )
    )
], timedelta(seconds=1), timedelta(seconds=5), 4, 4)
```

但要注意，嵌套之后，外层的回调函数获取到的`return_code`值来自于内层回调函数的返回值，而获取到的Item来自于外层的输入。

## 扩展：同时使用Downloader过滤和回调

同时使用了过滤和回调时，显然回调不会影响过滤函数的输入Item，进而也不会影响过滤过程；但反过来，过滤函数会影响到回调函数的输入参数。请看下例。

过滤器在外、回调函数在内时，回调的`download`在过滤器的`download`内调用，因此`callback`收到的就是已经过滤过的Item，没有什么异常：

```python
pair = Pair([SleepFeeder(0)], [
    RandomFilterDownloader(
        JustLogCallbackDownloader(
            SleepDownloader(0)
        )
    )
], timedelta(seconds=1), timedelta(seconds=5), 4, 4)
```

回调函数在外、过滤器在内时，过滤器的`download`在回调的`download`内调用，因此`callback`收到的是没有经过过滤的Item，且由于过滤器的`download`在要被过滤的Item处是直接退出的，所以在被过滤的Item处，`callback`收到的`return_code`值为`None`：

```python
pair = Pair([SleepFeeder(0)], [
    JustLogCallbackDownloader(
        RandomFilterDownloader(
            SleepDownloader(0)
        )
    )
], timedelta(seconds=1), timedelta(seconds=5), 4, 4)
```

从逻辑上看，我们不需要对一个没有经过下载的Item调用回调，其`return_code`值也没有意义，在此系统中还容易和正常退出的`return_code`混淆。所以过滤器在外，回调函数在内的用法才是逻辑上正确的用法。

为了避免同时使用过滤和回调的嵌套问题，索性定义了一个杂交类[`simplarchiver.FilterCallbackDownloader`](simplarchiver/abc.py)：

```python
class FilterCallbackDownloader(Downloader):
    """同时具有过滤和回调功能的Downloader"""

    def __init__(self, base_downloader: Downloader):
        """从一个基本的Downloader生成具有过滤和回调功能Downloader"""
        self.__base_downloader = base_downloader

    @abc.abstractmethod
    async def callback(self, item, return_code):
        """
        回调函数接受两个参数，一个是item，一个是被封装的基本Downloader的返回值
        """
        pass

    @abc.abstractmethod
    async def filter(self, item):
        """
        如果过滤器返回了None，则会被过滤掉，不会被Download
        过滤器内可以修改item
        """
        return item

    async def download(self, item):
        """过滤+回调"""
        item = await self.filter(item)
        if item is not None:  # 如果过滤器返回了None，则会被过滤掉，不会被Download
            return_code = await self.__base_downloader.download(item)
            await self.callback(item, return_code)
            return return_code  # 调用了回调之后将return_code继续向下一级返回
```

这个类就相当于一个过滤器在外、回调函数在内的嵌套。有了这个类，就没必要用过滤和回调实现既有过滤又有回调的Downloader了。尽量避免系统设计触及到已有系统的缺陷，不要为了图方便而用愚蠢的实现，在学习框架时好好从思想开始积累，在看到新框架时多多思考作者为什么要设计这样的框架、框架的基本思想是什么、使用者应该有一种什么样的共识、什么样的用法是好的、什么样的用法能解决问题但是不好、它不好在何处？是因为行为怪异难以捉摸而准备废弃？是因为开发时的疏忽而引入的不符合整体思想的实现？解决问题的方法千千万万，如果总是只采用查到的第一个方案作为解决方案而不经过对多种方案的思考和比较，那永远只能做代码的熟练搬运工，技术上永远不会有质的提升。不断追问解决方法背后的逻辑可以让人不由自主地去搜寻多种解决方案，即使有一个人云亦云的明显方案摆在眼前；在这样不断的在这种“无意义”的搜索上“浪费时间”的过程中，既有系统的核心思想和逻辑会逐渐地清晰，自己的对既有系统的直觉上的把握也会越来越接近作者的思维，解决问题的方式也会从“用网上搜到的解决方案”到“网上搜到的解决方案不太符合原作者的想法”到“自己思考解决方案”最后到“像原作者一样解决问题”。在不断的进步中你会逐渐发现搬运式编程的危害。一个优秀的系统可以让不同水平的使用者对一个相同的需求都写出大差不离的代码，这样即使不写注释其他人也能很容易地明白程序的意思，节约参与者的时间是开源项目大火的重要因素，如果一个开源项目目标明确，且只需要几分钟就能弄懂结构并按照自己的意愿添加功能，那只要它能解决某方面的需求，必定能成为优秀的开源项目。但这样优秀的系统难得一见，大部分情况下，大家都是用着“约定大于配置”的思想：程序这么写不是唯一的方法，也不一定是最好的方法，但我们在开发文档里约定大家就要这么写，不要自由发挥，那会让其他人在理解代码上浪费时间。大部分有名有姓的开源项目都是这么做的，因为这样可以极大地节约每个参与者的时间，更容易团结力量做大事。而搬运式编程则不符合这种套路。搬运式编程虽然能解决问题，但解决问题的方法都是一定条件下的产物，在计算机软件这一无比复杂的领域基本上不会有一种方法适用于多种情况。搬运式编程是“心中只有自己”甚至是心中只有“现在的自己”，连“未来维护程序时的自己”都没有，是一种目光短浅的做法。这种编程方式能极大地提升初期的开发效率，但遗患无穷。正确的方法是，不要搜索不到一个小时找到一个解决方案就欣喜若狂然后进入下一步，多搜索一些解决方案，多看看别人是的用法，读一读文档，体会一下作者的思想，看看自己站在作者的立场会做出什么样的东西，在回头看看作者是怎么解决问题的，最后再回头看看自己遇到的问题，这个问题为什么产生？原作者为什么没有在框架里直接解决问题？我的开发方法符合作者的思路吗？在不断的思考解决问题的过程中，自己的开发手法会逐渐熟练，知道哪些问题是可以避免的，框架在哪些情况不应该使用，更重要的是，你会发现网上能找到的大多数方案都是“愚蠢”的，贸然使用真的会带来更多的问题，从你发现这一情况的时刻开始，你解决问题的手法将发生质的变化，对所见方案的合理怀疑将成为你的本能，鉴别“愚蠢”方案将成为你的直觉，这种对“愚蠢”方案的抗拒将迫使你所用的一切框架和软件都倾尽所能进行深入挖掘，而越是深入，对网上那些方案的甄别能力就越强，更多似是而非的方案将浮出水面，强烈的违和感更加迫使你进行深入学习。这是一个正循环，当越过了那座山峰，接下来的进步自然而然。我自己是什么时候越过那座峰的？可能是在大一和几位志同道合的好友合作课设的时候，可能是在大二接触开源项目的时候，可能是在大三一个课设参加了好几个比赛的时候，也可能是在大四疫情在家一个人孤独地做毕设的时候。当我回过神来的时候，我发现自己hack开源项目越来越顺畅，阅读多人合作的开源代码就像读书一样自然，但写程序时的做法已经和身边的人越来越远，总觉得它们的程序虽然可以运行但无法交流，无法“读书”。困扰至此，反正这个垃圾项目也没有人看，随便乱写写。

## TODO

* 或许可以在不影响上层应用的情况下将过滤和回调改成接口类