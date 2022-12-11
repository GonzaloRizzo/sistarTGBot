import re
import logging
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


class SistarException(Exception):
    pass


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

                return {
                    "is_authorization": is_authorization,
                    "title": title,
                    "concepto": concepto,
                    "date": date,
                    "nro_cuota": nro_cuota,
                    "cant_cuota": cant_cuota,
                    "uyu": uyu,
                    "usd": usd,
                }
            else:
                ing = col1[4].getText().strip()
                mov = col1[6].getText().strip()

                uyu = col2[1].getText()
                usd = col3[1].getText()
                return {
                    "is_authorization": is_authorization,
                    "title": title,
                    "ing": ing,
                    "mov": mov,
                    "uyu": uyu,
                    "usd": usd,
                }

        return [_parse_row(row) for row in rows]
