from datetime import date
import json
import re
import requests
from urllib.parse import urljoin
from pydantic import BaseModel, validator
from typing import Literal

BASE_URL = "https://www.itaulink.com.uy/trx/"
RE_USERDATA = r"JSON.parse\('([^']*)'\)"


class ItauAccountTransaction(BaseModel):
    tipo: Literal["D", "C"] | str
    descripcion: str
    descripcionAdicional: str
    codigoFormulario: int
    fecha: date
    importe: float
    saldo: float

    @validator("fecha", pre=True)
    def validate_fecha(cls, field: dict):
        return field["millis"] / 1000

    def to_index(self):
        return frozenset({self.tipo, self.descripcion, self.fecha, self.importe})


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
    def validate_fecha(cls, field: dict):
        return field["millis"] / 1000

    @validator("tarjeta", pre=True)
    def validate_tarjeta(cls, field: dict):
        return field["hash"]

    def to_index(self):
        return frozenset(
            {
                self.fecha,
                self.tarjeta,
                self.nombreComercio,
                self.tipo,
                self.moneda,
                self.importe,
            }
        )


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

    def login(self, username, password):
        res = self.session.post(
            urljoin(BASE_URL, "doLogin"),
            data={
                "tipo_documento": "1",
                "tipo_usuario": "R",
                "nro_documento": username,
                "pass": password,
            },
        )
        match = re.findall(RE_USERDATA, res.text)[0]

        user_data = json.loads(match)

        self.user_accounts = ItauUserAccounts(**user_data["cuentas"])

    def fetch_card_authorizations(self, card_id) -> list[ItauAuthorization]:
        # /trx/tarjetas/credito/922e3a5a2ed7082eca4b9a27fb511971d823a52a4011a4e811dbd6abc79ddf42/autorizaciones_pendientes
        data = self._fetch(f"tarjetas/credito/{card_id}/autorizaciones_pendientes")
        autorizaciones = data["datos"]["datosAutorizaciones"]["autorizaciones"]
        return [ItauAuthorization(**a) for a in autorizaciones]
    
    def fetch_card_movements(self, card_id):
        pass

    def fetch_account_movements(self, account_id: str, year: int, month: int):

        today = date.today()

        if year == today.year and month == today.month:
            data = self._fetch(f"cuentas/1/{account_id}/mesActual")
            movements = data["movimientosMesActual"]["movimientos"]
        else:
            data = self._fetch(
                f"cuentas/1/{account_id}/{month}/{year-2000}/consultaHistorica"
            )
            movements = data["mapaHistoricos"]["movimientosHistoricos"]["movimientos"]

        return [ItauAccountTransaction(**m) for m in movements]

    def fetch_comprobante(self):
        # https://www.itaulink.com.uy/trx/cuentas/02/CRE.%20CAMBIOSOP....867135/23fea23c4c301fe09629a19668e3ccbcc5ac3afc535544eeaf2c72443885747d/30/NOV/2022/cargarComprobante
        pass

    def _fix_date(self, obj):
        return {**obj, "fecha": date.fromtimestamp(obj["fecha"]["millis"] / 1000)}
