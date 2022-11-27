import json
import logging
from datetime import timedelta

from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ContextTypes,
)

from SistarClient import SistarClient

log = logging.getLogger(__name__)


def movs_to_set(movs):
    return set(frozenset(m.items()) for m in movs)


class TelegramBotException(Exception):
    pass


class TelegramBot:
    def __init__(self, token, target_chat):

        self.token = token
        self.target_chat = target_chat
        self.application = Application.builder().token(token).build()
        self._load_last_poll()

    def _load_last_poll(self):
        try:
            with open("last_poll.json", "r") as f:
                self.last_poll_movements = json.load(f)
        except FileNotFoundError:
            self.last_poll_movements = []

    def _store_last_poll(self, last_poll):
        with open("last_poll.json", "w") as f:
            self.last_poll_movements = last_poll
            f.write(json.dumps(self.last_poll_movements, indent=4))

    def run(self):
        self.application.job_queue.run_once(self.do_polling, when=0)
        self.application.run_polling()

    async def do_polling(self, context: ContextTypes.DEFAULT_TYPE):
        diff = self._fetch_new_movements()
        await self._send_new_movements(diff)

        context.job_queue.run_once(self.do_polling, when=timedelta(minutes=30))
    
    def _get_text_for_movement(self, movement):
        text = f"<b>{movement['title']}</b>\n\n"

        if movement["is_authorization"]:
            text += movement["concepto"].replace("Concepto:", "<b>Concepto:</b>")
            text += "\n"
            text += movement["date"].replace("Fecha y Hora:", "<b>Date:</b>")
            text += "\n"
            text += movement["nro_cuota"].replace("Nro. Cuota:", "<b>Nro. Cuota:</b>")
            text += "\n"
            text += movement["cant_cuota"].replace("Cant. Cuotas:", "<b>Cant. Cuotas:</b>")
            text += "\n"
        else:
            text += movement["ing"].replace("Ing.", "<b>Ing:</b>")
            text += "\n"
            text += movement["mov"].replace("Mov.", "<b>Mov:</b>")
            text += "\n"
        
        text += "\n"
        
        if movement["uyu"] not in ["$ 0,00", "$ "]:
            text += movement['uyu'].replace("$", "<b>UYU:</b>")
            text += "\n"

        if movement["usd"] not in ["USD 0,00", "USD "]:
            text += movement['usd'].replace("USD", "<b>USD:</b>")
            text += "\n"
        
        return text

    async def _send_new_movements(self, new_movements):
        for movement in new_movements:
            log.info("Processing the following movement:")
            log.info(movement)

            text = self._get_text_for_movement(movement)

            log.info("Sending the following message:")
            log.info(text)

            await self.application.bot.send_message(
                chat_id=self.target_chat,
                parse_mode=ParseMode.HTML,
                text=text,
            )

    def _fetch_new_movements(self):
        c = SistarClient()
        c.login()

        movs = c.movimientos()

        diff_set = list(movs_to_set(movs) - movs_to_set(self.last_poll_movements))

        diff = [dict(d) for d in diff_set]

        self._store_last_poll(movs)

        return diff
