import json
from os import environ
from datetime import date
from urllib.parse import urljoin
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, validator
from playwright.sync_api import sync_playwright

from .base import BaseProvider

if TYPE_CHECKING:
    from ..config import ItauCardAuthorizationsAccount, ItauBankAccount

BASE_URL = "https://www.itaulink.com.uy/trx/"


class ItauAccountTransaction(BaseModel):
    tipo: Literal["D", "C"] | str
    fecha: date
    descripcion: str
    importe: float

    descripcionAdicional: str
    codigoFormulario: int  # What is this?
    saldo: float

    @validator("fecha", pre=True)
    def validate_fecha(cls, field):
        if isinstance(field, dict):
            return field["millis"] / 1000
        elif isinstance(field, date):
            return field
        elif isinstance(field, str):
            return field

    def matches(self, other):
        return all(
            [
                self.tipo == other.tipo,
                self.fecha == other.fecha,
                self.descripcion
                == other.descripcion,  # This one should be similar, not necesary equal for it to match
                # self.descripcionAdicional == other.descripcionAdicional, # Unfortunately this one do change
                self.importe == other.importe,
            ]
        )

    def format(self):
        text = f"<b>{self.tipo} {self.descripcion} {self.descripcionAdicional}</b>\n"
        text += "\n"
        text += f"<b>Fecha:</b> {self.fecha}\n"
        text += "\n"
        text += f"<b>Importe:</b> {self.importe}\n"
        return text


class ItauCardAuthorization(BaseModel):
    tipo: Literal["COMPRA"] | str
    fecha: date
    tarjeta: str
    importe: float
    nombreComercio: str
    moneda: Literal["Dolares", "Pesos"] | str

    hora: str
    nroReserva: str
    nroRespuesta: int
    etiqueta: Literal["Aprobada", "Negada"] | str
    aprobada: bool

    @validator("fecha", pre=True)
    def validate_fecha(cls, field):
        if isinstance(field, dict):
            return field["millis"] / 1000
        elif isinstance(field, date):
            return field
        elif isinstance(field, str):
            return field

    @validator("tarjeta", pre=True)
    def validate_tarjeta(cls, field):
        if isinstance(field, dict):
            return field["hash"]
        elif isinstance(field, str):
            return field

    def matches(self, other):
        # I can probably use Annotated in order to automate the declaration of which fields should be equal
        # Which ones DO change, which ones SHOULD stay equal, and which ones MUST stay equal

        # It's important when I integrate this with beancount that I also detect when some transaction matches, but has changed in some way

        # TODO: Sort by precedence
        return all(
            [
                self.tipo == other.tipo,
                self.fecha == other.fecha,
                self.tarjeta == other.tarjeta,
                self.importe == other.importe,
                self.nombreComercio == other.nombreComercio,
                self.moneda == other.moneda,
            ]
        )

    def format(self):
        text = f"<b>{self.tipo} {self.nombreComercio}: {self.etiqueta}</b>\n"
        text += "\n"
        text += f"<b>Fecha:</b> {self.fecha} {self.hora}\n"
        text += "\n"
        text += f"<b>{self.moneda}:</b> {self.importe}\n"

        return text


class ItauProvider(BaseProvider):
    def __init__(self, credentials_env) -> None:
        self.playwright = None
        self.browser = None
        self.context = None

        self.credentials_env = credentials_env

    def __repr__(self):
        return f"<ItauProvider {self.credentials_env=}>"

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.context = self.browser.new_context()

        username, password = environ[self.credentials_env].split(":")
        self._login(username, password)

    def stop(self):
        assert self.playwright, "ItauProvider not started"

        self.playwright.stop()

        self.playwright = None
        self.browser = None
        self.context = None

    def _fetch(self, url):
        assert self.context, "ItauProvider not started"
        res = self.context.request.get(urljoin(BASE_URL, url))

        body = res.body().decode("latin-1")

        return json.loads(body)["itaulink_msg"]["data"]

    def _login(self, username: str, password: str):
        assert self.context, "ItauProvider not started"

        page = self.context.new_page()
        page.goto(BASE_URL)

        page.type("#documento", username)
        page.type("#pass", password)

        page.click("#vprocesar")

    def fetch_itau_card_authorizations(self, account: "ItauCardAuthorizationsAccount"):
        data = self._fetch(f"tarjetas/credito/{account.id}/autorizaciones_pendientes")
        autorizaciones = data["datos"]["datosAutorizaciones"]["autorizaciones"]

        return [ItauCardAuthorization(**a) for a in autorizaciones]

    def fetch_itau_bank_account(self, account: "ItauBankAccount"):
        data = self._fetch(f"cuentas/1/{account.id}/mesActual")
        movements = data["movimientosMesActual"]["movimientos"]

        return [ItauAccountTransaction(**m) for m in movements]
