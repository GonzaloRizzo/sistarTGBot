import asyncio
import logging
from dotenv import load_dotenv
from os import getenv
from rich import print
from tg_bank_forwarder.sources.itau import itau_source
from tg_bank_forwarder.sources.sistarbank import sisterbank_source
from tg_bank_forwarder.bot import TelegramBot

load_dotenv()
LOGLEVEL = getenv("LOGLEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=LOGLEVEL
)


async def main():
    token = getenv("TG_TOKEN")
    target_chat = getenv("TG_TARGET_CHAT")

    SIS_DOC = getenv("SIS_DOC")
    SIS_PASS = getenv("SIS_PASS")
    assert SIS_DOC and SIS_PASS, "Missing Sistarbank credentials"

    ITAU_ID = getenv("ITAU_ID")
    ITAU_PASS = getenv("ITAU_PASS")
    assert ITAU_ID and ITAU_PASS, "Missing Itau credentials"

    bot = TelegramBot(token, target_chat)

    # bot.register_source(sisterbank_source(SIS_DOC, SIS_PASS))
    bot.register_source(
        itau_source(
            ITAU_ID,
            ITAU_PASS,
            [
                "23fea23c4c301fe09629a19668e3ccbcc5ac3afc535544eeaf2c72443885747d",
                "4d921396e8894d1f4d783585cc77cc5d1d45c27e1c381f66f379643ec2f57be8",
            ],
            ["922e3a5a2ed7082eca4b9a27fb511971d823a52a4011a4e811dbd6abc79ddf42"],
        )
    )

    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
