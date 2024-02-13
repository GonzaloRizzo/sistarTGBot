from .provider_cache import ProviderCache
from .config import Config

from rich import print

from time import sleep





TIME_30M = 60 * 30

class TGBankForwarderBot:
    def __init__(self, config_path):
        self.config = Config.read_config(config_path)

    def check_accounts(self):
        # SessionProviderCache
        provider_cache = ProviderCache()
        for (provider_name, credentials_env), accounts in self.config.group_accounts():
            # I think provider cache may not be needed
            # Since accounts are grouped, each cycle of this loop contains the only time
            #  a provider session will be needed

            provider = provider_cache.get(provider_name, credentials_env)
            print("####")
            print(provider)
            provider.start() # Turn this into a context manager

            for account in accounts:
                # with provider.new_transactions(account) as transactions:
                # with account.new_transactions as transactions:
                

                print("-----")
                print(account)
                # transactions = provider.get_transactions_for_account(account)
                # transactions = provider.get_new_transactions(account)
                diff = provider.compare_transactions(account)
                print(diff)

                # send_transactions(new_transactions)
            provider.stop()

    def loop(self):
        while True:
            self.check_accounts()
            sleep(TIME_30M)