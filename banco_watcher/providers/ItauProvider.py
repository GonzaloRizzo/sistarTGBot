from typing import Literal
from pydantic import BaseModel, SecretStr

from banco_watcher.clients.ItauClient import (
    ItauAccountMovement,
    ItauClient,
    ItauAuthorization,
)

from .base import BaseEntry, BaseProvider, Account


class ItauAccountEntry(BaseEntry, ItauAccountMovement):
    def as_tuple(self) -> tuple:
        return (self.fecha, self.saldo, self.importe, self.descripcion)

    def format(self):
        text = f"<b>{self.tipo} {self.descripcion} {self.descripcionAdicional}</b>\n"
        text += "\n"
        text += f"<b>Fecha:</b> {self.fecha}\n"
        text += "\n"
        text += f"<b>Importe:</b> {self.importe}\n"
        return text


class ItauAuthorizationEntry(BaseEntry, ItauAuthorization):
    def as_tuple(self) -> tuple:
        return (self.fecha, self.tarjeta, self.importe, self.nombreComercio)

    def format(self):
        text = f"<b>{self.tipo} {self.nombreComercio}: {self.etiqueta}</b>\n"
        text += "\n"
        text += f"<b>Fecha:</b> {self.fecha} {self.hora}\n"
        text += "\n"
        text += f"<b>{self.moneda}:</b> {self.importe}\n"

        return text


class ItauProviderAccount(BaseModel):
    id: str
    title: str
    type: Literal["account"] | Literal["card_authorizations"] | Literal[
        "card_movements"
    ]


class ItauProvider(BaseProvider):
    id: str
    username: str
    password: SecretStr
    accounts: list[ItauProviderAccount]

    def fetch_accounts(self):
        client = ItauClient()
        client.login(self.username, self.password.get_secret_value())

        for account in self.accounts:
            if account.type == "account":
                yield Account(
                    ":".join(["itau", self.id, account.id]),
                    ItauAccountEntry,
                    client.fetch_account_movements(account.id),
                )
            elif account.type == "card_authorizations":
                yield Account(
                    ":".join(["itau", self.id, account.id]),
                    ItauAuthorizationEntry,
                    client.fetch_card_authorizations(account.id),
                )
            # elif account.type == "card_movements":
            #     yield Account(":".join([self.id, account.id]), ItauAccountEntry, client.fetch_card_movements(account.id))
