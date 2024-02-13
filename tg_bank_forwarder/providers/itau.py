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
    descripcion: str
    descripcionAdicional: str
    codigoFormulario: int
    fecha: date
    importe: float
    saldo: float

    @validator("fecha", pre=True)
    def validate_fecha(cls, field):
        if isinstance(field, dict):
            return field["millis"] / 1000
        elif isinstance(field, date):
            return field
        elif isinstance(field, str):
            return field


class ItauCardAuthorization(BaseModel):
    fecha: date
    tarjeta: str
    hora: str
    nombreComercio: str
    tipo: Literal["COMPRA"] | str
    moneda: Literal["Dolares", "Pesos"] | str
    importe: float
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
