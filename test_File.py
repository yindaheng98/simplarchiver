import os
import asyncio
import logging
from datetime import timedelta

from simplarchiver import Pair, FilterDownloader
from simplarchiver.example import FileFeeder, DirFeeder, WalkFeeder, ExtFilterFeeder, JustDownloader
from simplarchiver.example import QBittorrentDownloader
from test_secret import qb_data

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s | %(name)-24s | %(message)s')

ttrss_feeders = [
    FileFeeder('./simplarchiver'),
    DirFeeder('./simplarchiver'),
    WalkFeeder('./simplarchiver'),
    ExtFilterFeeder(FileFeeder(qb_data['torrent_dir']), '.torrent')
]


class QBItemFilterDownloader(FilterDownloader):

    async def filter(self, item):
        if os.path.splitext(item)[1].lower() != '.torrent':
            return None
        return {
            'torrent_files': item,
            'save_path': qb_data['save_path_gen'](item),
        }


just_downloaders = [QBItemFilterDownloader(JustDownloader(i)) for i in range(1, 4)]
just_downloaders = [QBItemFilterDownloader(QBittorrentDownloader(**qb_data['opt']))]
pair = Pair(ttrss_feeders,
            just_downloaders,
            timedelta(seconds=5), 4, 8)
logging.info('pair.coroutine_once()')
asyncio.run(pair.coroutine_once())
