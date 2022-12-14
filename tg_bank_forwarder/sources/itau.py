import json
from datetime import date
from tg_bank_forwarder.clients.ItauClient import (
    ItauAccountTransaction,
    ItauAuthorization,
    ItauClient,
)

from .base import BaseSource

# It would be useful to cache clients on the same run.
# So a Source can define it's client and the poller could create it and pass it to all Sources that require the same Client


class ItauAuthorizationsSource(BaseSource):
    def __init__(self, username, password, card_id) -> None:
        self.username = username
        self.password = password
        self.card_id = card_id

    @property
    def index_keys(self) -> list:
        return ["fecha", "tarjeta", "nombreComercio", "tipo", "moneda", "importe"]

    def fetch(self) -> list:
        itau = ItauClient()
        itau.login(self.username, self.password)

        return [
            json.loads(auth.json())
            for auth in itau.fetch_card_authorizations(self.card_id)
        ]

    def format(self, value: dict):
        authorization = ItauAuthorization.parse_obj(value)
        text = f"<b>{authorization.tipo} {authorization.nombreComercio}: {authorization.etiqueta}</b>\n"

        text += "\n"

        text += f"<b>Fecha:</b> {authorization.fecha} {authorization.hora}\n"

        text += "\n"

        text += f"<b>{authorization.moneda}:</b> {authorization.importe}\n"

        return text


class ItauAccountTransactionSource(BaseSource):
    def __init__(self, username, password, account_id, moneda) -> None:
        self.username = username
        self.password = password
        self.account_id = account_id
        self.moneda = moneda

    @property
    def index_keys(self) -> list:
        return ["fecha", "tarjeta", "nombreComercio", "tipo", "moneda", "importe"]

    def fetch(self) -> list:
        itau = ItauClient()
        itau.login(self.username, self.password)

        today = date.today()

        return [
            json.loads(auth.json())
            for auth in itau.fetch_account_movements(
                self.account_id, today.year, today.month
            )
        ]

    def format(self, value):
        movement = ItauAccountTransaction.parse_obj(value)
        text = f"<b>{movement.tipo} {movement.descripcion} {movement.descripcionAdicional}</b>\n"

        text += "\n"

        text += f"<b>Fecha:</b> {movement.fecha}\n"

        text += "\n"

        text += f"<b>Importe:</b> {movement.importe} {self.moneda}\n"

        return text
