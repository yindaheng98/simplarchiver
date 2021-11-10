import os
import asyncio
import logging
from datetime import timedelta

from simplarchiver import Pair, Filter, Downloader, FilterDownloader
from simplarchiver.example import JustDownloader
from simplarchiver.example.file import FileFeeder, DirFeeder, WalkFeeder, ExtFilterFeeder
from simplarchiver.example.qbittorrent import QBittorrentDownloader
from test_secret import qb_data

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s | %(name)-24s | %(message)s')

ttrss_feeders = [
    FileFeeder('./simplarchiver'),
    DirFeeder('./simplarchiver'),
    WalkFeeder('./simplarchiver'),
    ExtFilterFeeder(FileFeeder(qb_data['torrent_dir']), '.torrent')
]


class QBItemFilter(Filter):

    async def filter(self, item):
        if os.path.splitext(item)[1].lower() != '.torrent':
            return None
        return {
            'torrent_files': item,
            'save_path': qb_data['save_path_gen'](item),
        }


def QBItemFilterDownloader(base_downloader: Downloader):
    return FilterDownloader(base_downloader, QBItemFilter())


just_downloaders = [QBItemFilterDownloader(JustDownloader(i)) for i in range(1, 4)]
just_downloaders = [QBItemFilterDownloader(QBittorrentDownloader(**qb_data['opt']))]
pair = Pair(ttrss_feeders,
            just_downloaders,
            timedelta(seconds=5), 4, 8)
logging.info('pair.coroutine_once()')
asyncio.run(pair.coroutine_once())
