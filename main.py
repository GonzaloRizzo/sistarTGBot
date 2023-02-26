import sentry_sdk
import asyncio
import logging
from dotenv import load_dotenv
from os import getenv

from banco_watcher.bot import BancoWatcherBot

load_dotenv()
SENTRY_DSN = getenv("SENTRY_DSN")
LOGLEVEL = getenv("LOGLEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=LOGLEVEL
)

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
    )

async def main():
    bot = BancoWatcherBot("config.json")
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
