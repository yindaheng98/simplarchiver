import asyncio
import logging

import qbittorrentapi

from simplarchiver import Downloader


class QBittorrentDownloader(Downloader):
    """用qBittorrent Web API下载种子文件"""

    def __init__(self, logger=logging.getLogger("FileFeeder"), **qb_cli_opt):
        """qb_cli_opt是用于运行时创建qbittorrentapi.client.Client的输入参数"""
        self.qb_cli_opt = qb_cli_opt
        self.__logger = logger

    def __torrent_add(self, kwargs):
        qbt_client = qbittorrentapi.Client(**self.qb_cli_opt)
        qbt_client.auth_log_in()
        return qbt_client.torrents_add(**kwargs)

    async def download(self, item):
        """下载输入的item实际上是qbittorrentapi.Client。torrents_add的输入参数**kwargs"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.__torrent_add, item)
