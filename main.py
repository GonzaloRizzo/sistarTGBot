import asyncio
import logging
from dotenv import load_dotenv
from os import getenv
from rich import print
from tg_bank_forwarder.sources.sistarbank import SisterbankSource
from tg_bank_forwarder.bot import TelegramBot

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def main():
    token = getenv("TG_TOKEN")
    target_chat = getenv("TG_TARGET_CHAT")

    bot = TelegramBot(token, target_chat)

    SIS_DOC = getenv("SIS_DOC")
    SIS_PASS = getenv("SIS_PASS")
    bot.register_source("sisterbank", SisterbankSource(SIS_DOC, SIS_PASS))

    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
