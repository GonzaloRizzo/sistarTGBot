import backoff
from datetime import date
import requests
from urllib.parse import urljoin
from pydantic import BaseModel, validator
from typing import Literal, Optional

BASE_URL = "https://www.itaulink.com.uy/trx/"
RE_USERDATA = r"JSON.parse\('([^']*)'\)"


class ItauAccountMovement(BaseModel):
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


class ItauAuthorization(BaseModel):
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


class ItauAccount(BaseModel):
    hash: str
    tipoCuenta: int
    idCuenta: str
    moneda: Literal["US.D", "URGP"] | str
    nombreTitular: str
    saldo: float
    customer: str
    hashCustomer: str


class ItauUserAccounts(BaseModel):
    caja_de_ahorro: list[ItauAccount]
    cuenta_corriente: list[ItauAccount]
    cuenta_recaudadora: list[ItauAccount]
    cuenta_de_alimentacion: list[ItauAccount]


class ItauClient:
    user_accounts: ItauUserAccounts | None = None
    session: requests.Session

    def __init__(self):
        self.session = requests.Session()

    def _fetch(self, path, data=None):
        res = self.session.post(urljoin(BASE_URL, path), data=data)

        return res.json()["itaulink_msg"]["data"]

    @backoff.on_exception(
        backoff.expo, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
    )
    def login(self, username=None, password=None):
        res = requests.get("http://itau-service:3000/login")

        cookies = res.json()['cookies']
        self.session.cookies.set("TS01888778", cookies["TS01888778"], domain="www.itaulink.com.uy")
        self.session.cookies.set("JSESSIONID", cookies["JSESSIONID"], domain="www.itaulink.com.uy")

    def fetch_card_authorizations(self, card_id) -> list[ItauAuthorization]:
        # /trx/tarjetas/credito/922e3a5a2ed7082eca4b9a27fb511971d823a52a4011a4e811dbd6abc79ddf42/autorizaciones_pendientes

        data = self._fetch(f"tarjetas/credito/{card_id}/autorizaciones_pendientes")
        autorizaciones = data["datos"]["datosAutorizaciones"]["autorizaciones"]

        return [ItauAuthorization(**a) for a in autorizaciones]

    def fetch_card_movements(self, card_id):
        pass

    def fetch_account_movements(
        self, account_id: str, year: Optional[int] = None, month: Optional[int] = None
    ):
        assert (year is None and month is None) or (
            year is not None and month is not None
        ), "Must send Year and Month or not send either"

        today = date.today()

        if (year == today.year and month == today.month) or (
            year is None and month is None
        ):
            data = self._fetch(f"cuentas/1/{account_id}/mesActual")
            movements = data["movimientosMesActual"]["movimientos"]
        else:
            data = self._fetch(
                f"cuentas/1/{account_id}/{month}/{year-2000}/consultaHistorica"
            )
            movements = data["mapaHistoricos"]["movimientosHistoricos"]["movimientos"]

        return [ItauAccountMovement(**m) for m in movements]

    def fetch_comprobante(self):
        # https://www.itaulink.com.uy/trx/cuentas/02/CRE.%20CAMBIOSOP....867135/23fea23c4c301fe09629a19668e3ccbcc5ac3afc535544eeaf2c72443885747d/30/NOV/2022/cargarComprobante
        pass

    def _fix_date(self, obj):
        return {**obj, "fecha": date.fromtimestamp(obj["fecha"]["millis"] / 1000)}
