from itertools import groupby
from time import sleep
from typing import TYPE_CHECKING

import sentry_sdk
import telebot
from rich import print

from .providers import provider_registry
from .config import Config

if TYPE_CHECKING:
    from .config import Account

TIME_30M = 60 * 30


class TGBankForwarderBot:
    def __init__(self, config_path):
        self.config = Config.read_config(config_path)
        self.telegram = telebot.TeleBot(self.config.token, parse_mode="html")

    def grouped_accounts(self):
        """
        Groups accounts so if the provider and the credentials are the same, we reuse the session
        """

        return groupby(self.config.accounts, lambda a: (a.provider, a.credentials_env))

    def check_accounts(self):
        for (provider_name, credentials_env), accounts in self.grouped_accounts():
            provider = provider_registry[provider_name](credentials_env)
            print(f"{provider=}")

            # TODO: Turn this into a context manager
            provider.start()

            for account in accounts:
                try:
                    print(f"{account=}")

                    new_transactions = provider.get_new_transactions(account)
                    print(f"{new_transactions=}")

                    self.send_transactions(account, new_transactions)

                except Exception as err:
                    sentry_sdk.capture_exception(err)
                    self.send_error(account, err)

            provider.stop()

    def send_error(self, account: "Account", err: Exception):
        text = f"{account.name} failied:\n{str(err)}"
        self.telegram.send_message(self.config.target_chat, text)

    def send_transactions(self, account, new_transactions):
        for transaction in new_transactions:
            text = f"<u>{account.name}</u>\n"
            text += "\n"
            text += transaction.format()

            self.telegram.send_message(self.config.target_chat, text)

    def loop(self):
        while True:
            self.check_accounts()
            sleep(TIME_30M)
