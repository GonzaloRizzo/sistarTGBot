from operator import lt
from pydantic import SecretStr
from banco_watcher.clients.SistarbancClient import (
    SistarbancAuthorization,
    SistarbancClient,
    SistarbancMovement,
)
from .base import BaseEntry, BaseProvider, Account

DATE_FORMAT = "%d/%m/%y"
DATETIME_FORMAT = f"{DATE_FORMAT} %H:%M:%S"


class SistarbancAuthorizationEntry(BaseEntry, SistarbancAuthorization):
    def format(self):
        installments = (
            f"{self.instalments[0]}/{self.instalments[1]}"
            if self.instalments[1] > 1
            else None
        )
        text = f"<b>{self.title} {installments}</b>\n"
        text += f"Date: {self.date.strftime(DATETIME_FORMAT)}\n"
        text += "\n"
        text += "\n"
        text += f"<b>{self.currency}: {self.amount}</b>"

        return text

    def as_tuple(self):
        return (self.card, self.date, self.id, self.title, self.amount, self.currency)


class SistarbancMovementEntry(BaseEntry, SistarbancMovement):
    def format(self):
        text = f"<b>{self.title}</b>\n"
        text += f"Mov: {self.mov.strftime(DATE_FORMAT)}\n"
        text += f"Ing: {self.ing.strftime(DATE_FORMAT)}\n"
        text += "\n"
        text += "\n"
        text += f"<b>{self.currency}: {self.amount}</b>"

        return text

    def as_tuple(self):
        return (self.card, self.title, self.mov, self.ing, self.amount, self.currency)


class SistarbancProvider(BaseProvider):
    id: str
    username: str
    password: SecretStr

    def fetch_accounts(self):
        client = SistarbancClient()
        client.login(self.username, self.password.get_secret_value())

        return [
            Account(
                ":".join(["sistarbanc", self.id, "autorizaciones"]),
                SistarbancAuthorizationEntry,
                client.autorizaciones(),
            ),
            Account(
                ":".join(["sistarbanc", self.id, "movimientos"]),
                SistarbancMovementEntry,
                client.movimientos(),
            ),
        ]
