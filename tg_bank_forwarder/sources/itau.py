from datetime import date
from tg_bank_forwarder.clients.ItauClient import (
    ItauAccountTransaction,
    ItauAuthorization,
    ItauClient,
)


def itau_source(
    username: str, password: str, account_ids: dict[str, str], card_ids: dict[str, str]
):
    def poll():
        itau = ItauClient()
        itau.login(username, password)

        for account_id, title in account_ids.items():
            today = date.today()
            yield (
                f"itau:account:{account_id}",
                itau.fetch_account_movements(account_id, today.year, today.month),
                ItauAccountTransaction,
                title,
            )

        for card_id, title in card_ids.items():
            yield (
                f"itau:card_authorization:{card_id}",
                itau.fetch_card_authorizations(card_id),
                ItauAuthorization,
                title,
            )

    return poll
