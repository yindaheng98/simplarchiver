# simplarchiver
一个简单的可扩展聚合异步下载器框架（Python协程小练习）

简单到只有两种自定义的组件：
* feeder：获取要下载的items
* downloader：接收feeder给的items，进行下载

和一个核心组件controller。核心组件的功能是：
* 调用feeder获取要下载的items，调用downloader进行下载
* 维护一个feeder-downloader对列表
* 定时执行feeder-downloader对列表中的下载任务
* 维护feeder和downloader的任务队列及线程池

程序执行的流程如下：
1. 创建downloader下载队列，启动downloader等待下载
2. 启动feeder获取要下载的items
3. 对于每个item，在所有的downloader下载队列里面放一个
4. items发完之后向每个downloader下载队列发送None作为停止信号
5. downloader运行完所有的下载任务后收到最后的停止信号就退出
6. feeder等待所有downloader退出
7. sleep指定的时间，回到步骤1

一些例程可以参见`example`和`test_*.py`。