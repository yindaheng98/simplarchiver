import time

from simplarchiver.abc import *
from simplarchiver.example import *
from datetime import timedelta
import logging
import asyncio

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s | %(levelname)-8s | %(name)-26s | %(message)s')

root = Root()
b = root.next(SleepFeeder(0)).next(SleepFliter(1)).next(SleepAmplifier(1)).next(Branch())
b.next(SleepDownloader(0))
b.next(SleepDownloader(1))
async def main():
    await root(123)
    await root.join()
asyncio.run(main())
print("sleeping")
time.sleep(10)

chain = Chain()
chain.next(SleepFeeder(0)).next(SleepFliter(1)).next(SleepAmplifier(1)).next(SleepDownloader(0))
async def main():
    await chain(123)
    await chain.join()
asyncio.run(main())
print("sleeping")
time.sleep(10)
