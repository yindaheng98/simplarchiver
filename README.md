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