from itertools import groupby

from .providers import provider_registry
from .config import Config

from rich import print

from time import sleep


TIME_30M = 60 * 30


class TGBankForwarderBot:
    def __init__(self, config_path):
        self.config = Config.read_config(config_path)

    def grouped_accounts(self):
        """
        Groups accounts so if the provider and the credentials are the same, we reuse the session
        """

        return groupby(
            self.config.accounts, lambda a: (a.provider, a.credentials_env)
        )

    def check_accounts(self):
        for (provider_name, credentials_env), accounts in self.grouped_accounts():
            provider = provider_registry[provider_name](credentials_env)
            print("provider", provider)
            
            # TODO: Turn this into a context manager
            provider.start() 

            for account in accounts:

                print("account", account)
                diff = provider.compare_transactions(account)
                print(diff)

                # send_transactions(new_transactions)
            provider.stop()

    def loop(self):
        while True:
            self.check_accounts()
            sleep(TIME_30M)
