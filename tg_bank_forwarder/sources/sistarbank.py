from tg_bank_forwarder.clients.SistarClient import SistarClient

from .base import BaseSource


class SisterbankSource(BaseSource):
    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password

    @property
    def index_keys(self) -> list:
        return ["date", "title", "uyu", "usd"]

    def fetch(self) -> list:
        c = SistarClient()
        c.login(self.username, self.password)

        return c.movimientos()

    def format(self, movement):
        text = f"<b>{movement['title']}</b>\n\n"

        if movement["is_authorization"]:
            text += movement["concepto"].replace("Concepto:", "<b>Concepto:</b>")
            text += "\n"
            text += movement["date"].replace("Fecha y Hora:", "<b>Date:</b>")
            text += "\n"
            text += movement["nro_cuota"].replace("Nro. Cuota:", "<b>Nro. Cuota:</b>")
            text += "\n"
            text += movement["cant_cuota"].replace(
                "Cant. Cuotas:", "<b>Cant. Cuotas:</b>"
            )
            text += "\n"
        else:
            text += movement["ing"].replace("Ing.", "<b>Ing:</b>")
            text += "\n"
            text += movement["mov"].replace("Mov.", "<b>Mov:</b>")
            text += "\n"

        text += "\n"

        if movement["uyu"] not in ["$ 0,00", "$ "]:
            text += movement["uyu"].replace("$", "<b>UYU:</b>")
            text += "\n"

        if movement["usd"] not in ["USD 0,00", "USD "]:
            text += movement["usd"].replace("USD", "<b>USD:</b>")
            text += "\n"

        return text
