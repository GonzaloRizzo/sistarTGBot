
from pydantic import BaseModel
from typing import TYPE_CHECKING

from ..transaction_cache import load_transactions, store_transactions

if TYPE_CHECKING:
    from ..config import Account


class BaseProvider():
    def start(self):
        pass
    def stop(self):
        pass

    def get_transactions_for_account(self, account: "Account") -> list[BaseModel]:
        return getattr(self, f"fetch_{account.type}")(account)
    
    def get_new_transactions(self, account: "Account"):
        current_transactions = self.get_transactions_for_account(account)
        cached_transactions = load_transactions(account)

        store_transactions(account, current_transactions)

        # new_transactions = {k:list(v) for k, v in groupby(cached_transactions, lambda t: [t.card, t.title, t.mov, t.cu t.amount, t.currency])}

        return current_transactions
        