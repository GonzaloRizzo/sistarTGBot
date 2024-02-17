from typing import TYPE_CHECKING

from pydantic import BaseModel

from ..transaction_cache import load_transactions, store_transactions

if TYPE_CHECKING:
    from ..config import Account


class BaseProvider:
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def get_transactions_for_account(self, account: "Account") -> list[BaseModel]:
        # mypy doesn't love getattr
        return getattr(self, f"fetch_{account.type}")(account)

    def compare_transactions(self, account: "Account"):
        current_transactions = self.get_transactions_for_account(account)
        cached_transactions = load_transactions(account)

        store_transactions(account, current_transactions)

        # new_transactions = {k:list(v) for k, v in groupby(cached_transactions, lambda t: [t.card, t.title, t.mov, t.cu t.amount, t.currency])}

        transaction_mapping = []
        new_transactions = []  # unmtched

        for cu_t in current_transactions:
            # try to find a match in the cache.

            try:
                matching_index = next(
                    index
                    for index, ca_t in enumerate(cached_transactions)
                    if ca_t.matches(cu_t)
                )
                ca_t = cached_transactions.pop(matching_index)
                transaction_mapping.append((cu_t, ca_t))

            except StopIteration:
                new_transactions.append(cu_t)

        deletions = cached_transactions  # Any transaction left on the cache list has been deleted, since it wasn't matched
        matches = [
            cu_t for cu_t, ca_t in transaction_mapping
        ]  # Take the cu_t from the mapping given that even if they match, cu_t is fresh
        additions = new_transactions  # By Definition

        diff = {
            "-": deletions,
            "=": matches,
            "+": additions,
        }
        print(diff)
        return diff

    def get_new_transactions(self, account: "Account"):
        return self.compare_transactions(account)["+"]
