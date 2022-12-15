from datetime import date
from tg_bank_forwarder.clients.ItauClient import (
    ItauAccountTransaction,
    ItauAuthorization,
    ItauClient,
)


def itau_source(
    username: str, password: str, account_ids: list[str], card_ids: list[str]
):
    def poll():
        itau = ItauClient()
        itau.login(username, password)

        for account_id in account_ids:
            today = date.today()
            yield (
                f"itau:account:{account_id}",
                itau.fetch_account_movements(account_id, today.year, today.month),
                ItauAccountTransaction,
            )

        for card_id in card_ids:
            yield (
                f"itau:card_authorization:{card_id}",
                itau.fetch_card_authorizations(card_id),
                ItauAuthorization,
            )

    return poll
