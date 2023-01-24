import html
import re
import logging
from typing import Optional
import requests
from bs4 import BeautifulSoup

from tg_bank_forwarder.sources.base import BaseSourceModel

log = logging.getLogger(__name__)


class SistarException(Exception):
    pass


class SistarbankMovement(BaseSourceModel):
    is_authorization: bool
    title: str
    concepto: Optional[str]
    nro_cuota: Optional[str]
    cant_cuota: Optional[str]
    date: Optional[str]
    ing: Optional[str]
    mov: Optional[str]
    uyu: str
    usd: str

    def to_index(self):
        return frozenset({self.date, self.title, self.uyu, self.usd})

    def get_uyu(self) -> float | None:
        match = re.search(r"\$ (\d+,\d{2})", self.uyu)
        if not match:
            return

        return float(match.group(1).replace(",", "."))

    def get_usd(self) -> float | None:
        match = re.search(r"USD (\d+,\d{2})", self.uyu)
        if not match:
            return

        return float(match.group(1).replace(",", "."))

    def format(self):
        text = f"<b>{self.title}</b>\n\n"

        if self.is_authorization:
            assert (
                self.concepto and self.date and self.nro_cuota and self.cant_cuota
            ), "Missing values"
            text += self.concepto.replace("Concepto:", "<b>Concepto:</b>")
            text += "\n"
            text += self.date.replace("Fecha y Hora:", "<b>Date:</b>")
            text += "\n"
            text += self.nro_cuota.replace("Nro. Cuota:", "<b>Nro. Cuota:</b>")
            text += "\n"
            text += self.cant_cuota.replace("Cant. Cuotas:", "<b>Cant. Cuotas:</b>")
            text += "\n"
        else:
            assert self.ing and self.mov, "Missing values"
            text += self.ing.replace("Ing.", "<b>Ing:</b>")
            text += "\n"
            text += self.mov.replace("Mov.", "<b>Mov:</b>")
            text += "\n"

        text += "\n"

        uyu_value = self.get_uyu()
        usd_value = self.get_usd()
        is_expense = None
        mwiz_account = None
        mwiz_amount = None
        mwiz_currency = None

        if uyu_value and uyu_value != 0:
            is_expense = uyu_value > 0
            mwiz_account = "MastercardBROUUYU"
            mwiz_amount = uyu_value
            mwiz_currency = "UYU"
            text += f"<b>UYU: {uyu_value}</b>"
            text += "\n"

        elif usd_value and usd_value != 0:
            is_expense = usd_value > 0
            mwiz_account = "MastercardBROUUSD"
            mwiz_amount = usd_value
            mwiz_currency = "USD"
            text += f"<b>USD: {usd_value}</b>"
            text += "\n"

        mwiz_date = (
            re.sub(
                r"Fecha y Hora: (\d{2})/(\d{2})/(\d{2}) - ",
                r"20\3-\2-\1 ",
                self.date or "",
            )
            if self.is_authorization
            else re.sub(r"Mov\. (\d{2})/(\d{2})/(\d{2})", r"20\3-\2-\1", self.mov or "")
        )

        mwiz_url = f"moneywiz://{'expense' if is_expense else 'income'}?account={mwiz_account}&amount={mwiz_amount}&currency={mwiz_currency}&mwiz_description={self.concepto if self.is_authorization else self.title}&date={mwiz_date}"
        text += f'\n<a href="{html.escape(mwiz_url)}">Add to MoneyWiz</a>'

        return text


class SistarClient:
    def __init__(self):
        self.session = requests.Session()

        # self.session.headers.update(
        #     {
        #         "User-Agent": "sistarTGBot <sistarTGBot@gonzalorizzo.com> (https://github.com/GonzaloRizzo/sistarTGBot)"
        #     }
        # )
        self.cl = None

    def login(self, username, password):
        if not username or not password:
            raise SistarException("Missing credentials.")
        log.debug("Running login")
        home = self.session.get("https://brou.e-sistarbanc.com.uy/")
        tks = (
            BeautifulSoup(home.text, "lxml")
            .find("input", attrs={"name": "tks"})
            .attrs["value"]  # type: ignore
        )
        self.session.post(
            "https://brou.e-sistarbanc.com.uy/",
            data={
                "tks": tks,
                "documento": username,
                "password": password,
                "button1": "Ingresar",
            },
            allow_redirects=False,
        )
        inicio = self.session.get("https://brou.e-sistarbanc.com.uy/inicio/")
        cl = next(re.finditer(r"var cl = \'([^\']*)\'", inicio.text)).groups()[0]

        self.cl = cl

    def movimientos(self):
        return list(reversed(self._parse_movimientos_html(self.movimientos_html())))

    def movimientos_html(self):
        log.debug(f"Fetching movimientos")
        if not self.cl:
            raise SistarException("No CL found. Please login")

        inicio_ajax_response = self.session.get(
            "https://brou.e-sistarbanc.com.uy/url.php",
            params={"id": "inicioajax", "cl": self.cl},
        )
        p3 = (
            BeautifulSoup(inicio_ajax_response.text, "lxml")
            .find("input", attrs={"name": "p3"})
            .attrs["value"]  # type: ignore
        )
        movs = self.session.post(
            "https://brou.e-sistarbanc.com.uy/movimientos/", data={"p3": p3}
        )
        p3 = (
            BeautifulSoup(movs.text, "lxml")
            .find("input", attrs={"name": "p3"})
            .attrs["value"]  # type: ignore
        )

        movimientos_ajax_response = self.session.get(
            "https://brou.e-sistarbanc.com.uy/url.php",
            params={"id": "movimientosajax", "p3": p3, "cl": self.cl},
        )

        return movimientos_ajax_response.text

    def _parse_movimientos_html(self, html):
        bs = BeautifulSoup(html, "lxml")
        rows = bs.find_all("div", {"class": "cont-movimiento"})

        def _parse_row(row):
            cols = list(row.find("div").children)

            col1 = list(cols[1].children)
            col2 = list(cols[3].children)
            col3 = list(cols[5].children)

            title = col1[1].getText().strip()
            is_authorization = "A confirmar" in title
            if is_authorization:
                concepto = col1[4].getText().strip()
                date = col1[6].getText().strip()
                nro_cuota = col1[8].getText().strip()
                cant_cuota = col1[10].getText().strip()

                uyu = col2[1].getText()
                usd = col3[1].getText()

                return SistarbankMovement.parse_obj(
                    {
                        "is_authorization": is_authorization,
                        "title": title,
                        "concepto": concepto,
                        "date": date,
                        "nro_cuota": nro_cuota,
                        "cant_cuota": cant_cuota,
                        "uyu": uyu,
                        "usd": usd,
                    }
                )
            else:
                ing = col1[4].getText().strip()
                mov = col1[6].getText().strip()

                uyu = col2[1].getText()
                usd = col3[1].getText()
                return SistarbankMovement.parse_obj(
                    {
                        "is_authorization": is_authorization,
                        "title": title,
                        "ing": ing,
                        "mov": mov,
                        "uyu": uyu,
                        "usd": usd,
                    }
                )

        return [_parse_row(row) for row in rows]
