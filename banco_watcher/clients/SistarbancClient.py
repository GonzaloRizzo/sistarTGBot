from datetime import datetime
from typing import Literal
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup, Tag


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
    id: int
    card: str
    title: str

    date: datetime
    instalments: tuple[int, int]

    amount: float
    currency: Literal["USD"] | Literal["UYU"]

    @classmethod
    def parse_raw(cls, raw):
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


class SistarbancMovement(BaseModel):
    card: str
    title: str

    mov: datetime
    ing: datetime

    amount: float
    currency: Literal["USD"] | Literal["UYU"]

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


def table_to_py(table: Tag):
    output = []
    for trs in table.select("tr"):
        entry = []
        tds = trs.select("td")
        for td in tds:
            entry.append(td.text.strip())
        output.append(entry)

    return [dict(zip(output[0], raw)) for raw in output[1:]]


class SistarbancClient:
    def __init__(self) -> None:
        self.session = requests.Session()

    def login(self, username, password):
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

    def movimientos(self):
        html = self.session.get(
            "https://www.e-sistarbanc.com.uy/ac_movimientos_actuales.php"
        ).text

        bs = BeautifulSoup(html, "lxml")
        table = bs.select_one("#listado table")

        assert table, "Missing table"

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

    def autorizaciones(self):
        html = self.session.get(
            "https://www.e-sistarbanc.com.uy/ac_autorizaciones_pendientes.php"
        ).text

        bs = BeautifulSoup(html, "lxml")
        table = bs.select_one("#listado table")

        assert table, "Missing table"

        return [SistarbancAuthorization.parse_raw(e) for e in table_to_py(table)]
