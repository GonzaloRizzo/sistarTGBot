import asyncio
import logging
from dotenv import load_dotenv
from os import getenv
from rich import print
from tg_bank_forwarder.sources.itau import (
    ItauAccountTransactionSource,
    ItauAuthorizationsSource,
)
from tg_bank_forwarder.sources.sistarbank import SisterbankSource
from tg_bank_forwarder.bot import TelegramBot

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def main():
    token = getenv("TG_TOKEN")
    target_chat = getenv("TG_TARGET_CHAT")

    SIS_DOC = getenv("SIS_DOC")
    SIS_PASS = getenv("SIS_PASS")
    ITAU_PASS = getenv("ITAU_PASS")
    ITAU_ID = getenv("ITAU_ID")

    bot = TelegramBot(token, target_chat)

    bot.register_source("sisterbank", SisterbankSource(SIS_DOC, SIS_PASS))

    bot.register_source(
        "itau-authorization",
        ItauAuthorizationsSource(
            ITAU_ID,
            ITAU_PASS,
            "922e3a5a2ed7082eca4b9a27fb511971d823a52a4011a4e811dbd6abc79ddf42",
        ),
    )

    bot.register_source(
        "itau-account-usd",
        ItauAccountTransactionSource(
            ITAU_ID,
            ITAU_PASS,
            "23fea23c4c301fe09629a19668e3ccbcc5ac3afc535544eeaf2c72443885747d",
            "Dolares",
        ),
    )

    bot.register_source(
        "itau-account-uyu",
        ItauAccountTransactionSource(
            ITAU_ID,
            ITAU_PASS,
            "4d921396e8894d1f4d783585cc77cc5d1d45c27e1c381f66f379643ec2f57be8",
            "Pesos",
        ),
    )

    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
