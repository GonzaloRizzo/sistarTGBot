from datetime import datetime
from os import environ
from typing import TYPE_CHECKING, Literal

import requests
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel

from .base import BaseProvider

if TYPE_CHECKING:
    from ..config import SistarbancAuthorizationsAccount, SistarbancMovementsAccount

DATE_FORMAT = "%d/%m/%y"
DATETIME_FORMAT = f"{DATE_FORMAT} %H:%M:%S"


def table_to_py(table: Tag):
    output = []
    for trs in table.select("tr"):
        entry = []
        tds = trs.select("td")
        for td in tds:
            entry.append(td.text.strip())
        output.append(entry)

    return [dict(zip(output[0], raw)) for raw in output[1:]]


def parse_amount(amount_str: str):
    try:
        return float(amount_str.replace(",", "."))
    except ValueError:
        return None


def parse_amount_currency(uyu, usd):
    usd_amount = parse_amount(usd)
    uyu_amount = parse_amount(uyu)

    amount, currency = None, None
    if usd_amount and abs(usd_amount) > 0:
        amount, currency = usd_amount, "USD"
    elif uyu_amount and abs(uyu_amount) > 0:
        amount, currency = uyu_amount, "UYU"

    assert amount and currency, "Transaction amount and currency could not be defined"

    return amount, currency


class SistarbancAuthorization(BaseModel):
    id: int  # What's this?

    card: str
    date: datetime
    title: str
    amount: float
    currency: Literal["USD"] | Literal["UYU"]

    instalments: tuple[int, int]

    @classmethod
    def parse_raw(cls, raw):
        # TODO: Remove this, I can certainly use Alias and root_validator for those transformations
        date = datetime.strptime(f'{raw["Fecha"]} {raw["Hora"]}', "%d/%m/%y %H:%M:%S")

        amount, currency = parse_amount_currency(raw["$"], raw["USD"])

        return SistarbancAuthorization(
            id=raw["Autorización"],
            title=raw["Concepto"],
            date=date,
            card=raw["Tarjeta"],
            instalments=(
                raw["Nro. Cuota"],
                raw["Cant. Cuotas"],
            ),
            amount=amount,
            currency=currency,
        )

    def matches(self, other):
        return all(
            [
                # self.id == other.id,
                self.card == other.card,
                self.date == other.date,
                self.title == other.title,
                self.amount == other.amount,
                self.currency == other.currency,
            ]
        )

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


class SistarbancMovement(BaseModel):
    card: str
    ing: datetime
    title: str
    amount: float
    currency: Literal["USD"] | Literal["UYU"]

    mov: datetime

    @classmethod
    def parse_raw(cls, raw):
        mov = datetime.strptime(raw["Mov."], "%d/%m/%y")
        ing = datetime.strptime(raw["Ing."], "%d/%m/%y")

        amount, currency = parse_amount_currency(raw["$"], raw["USD"])

        return cls(
            title=raw["Concepto"],
            mov=mov,
            ing=ing,
            card=raw["Tarjeta"],
            currency=currency,
            amount=amount,
        )

    def matches(self, other):
        return all(
            [
                # self.id == other.id,
                self.card == other.card,
                self.ing == other.ing,
                self.title == other.title,
                self.amount == other.amount,
                self.currency == other.currency,
            ]
        )

    def format(self):
        text = f"<b>{self.title}</b>\n"
        text += f"Mov: {self.mov.strftime(DATE_FORMAT)}\n"
        text += f"Ing: {self.ing.strftime(DATE_FORMAT)}\n"
        text += "\n"
        text += "\n"
        text += f"<b>{self.currency}: {self.amount}</b>"

        return text


class SistarbancProvider(BaseProvider):
    def __init__(self, credentials_env) -> None:
        self.session = requests.Session()
        self.credentials_env = credentials_env

    def __repr__(self):
        return f"<SistarbancProvider {self.credentials_env=}>"

    def __enter__(self):
        username, password = environ[self.credentials_env].split(":")
        self._login(username, password)

        return self

    def __exit__(self, type, value, traceback):
        self.session.close()

    def _login(self, username, password):
        assert username and password, "Missing credentials."

        self.session.get("https://www.e-sistarbanc.com.uy/ingresar/")
        self.session.post(
            "https://www.e-sistarbanc.com.uy/ingresar/",
            data={
                "email_acc": username,
                "clave_acc": password,
                "btn_ingresar": "Ingresar",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://www.e-sistarbanc.com.uy/ingresar/",
            },
        )

    def fetch_sistarbanc_movements(self, account: "SistarbancMovementsAccount"):
        html = self.session.get(
            "https://www.e-sistarbanc.com.uy/ac_movimientos_actuales.php"
        ).text

        bs = BeautifulSoup(html, "lxml")

        content = bs.select_one(".maq_contenido.cuenta")
        assert content, "Missing content"

        table = content.select_one("#listado table")

        if not table:
            return []

        data = table_to_py(table)
        skiped_entries = [
            "TOTAL TARJETA",
            "SALDO AL ULTIMO CORTE",
            "SALDO REGISTRADO A LA FECHA",
        ]
        return [
            SistarbancMovement.parse_raw(e)
            for e in data
            if e["Concepto"] not in skiped_entries
        ]

    def fetch_sistarbanc_authorizations(
        self, account: "SistarbancAuthorizationsAccount"
    ):
        html = self.session.get(
            "https://www.e-sistarbanc.com.uy/ac_autorizaciones_pendientes.php"
        ).text

        bs = BeautifulSoup(html, "lxml")

        content = bs.select_one(".maq_contenido.cuenta")
        assert content, "Missing content"

        table = content.select_one("#listado table")

        if not table:
            return []

        return [SistarbancAuthorization.parse_raw(e) for e in table_to_py(table)]
