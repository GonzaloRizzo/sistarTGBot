import logging
from os import getenv

import sentry_sdk
from dotenv import load_dotenv

from tg_bank_forwarder.bot import TGBankForwarderBot

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


def main():
    bot = TGBankForwarderBot("config.yml")
    bot.loop()


if __name__ == "__main__":
    main()
