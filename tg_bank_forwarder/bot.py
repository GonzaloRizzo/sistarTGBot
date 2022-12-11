import json

from rich import print
from pathlib import Path
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telebot.async_telebot import AsyncTeleBot

from tg_bank_forwarder.sources.base import BaseSource


LAST_POLL_DIRECTORY = "last_polls"


def index_dict_array(array, index_keys):
    return set(
        frozenset((k, v) for k, v in dict.items() if k in index_keys) for dict in array
    )


class TelegramBot:
    def __init__(self, token, target_chat) -> None:
        self.scheduler = AsyncIOScheduler()

        self.bot = AsyncTeleBot(token, parse_mode="HTML")
        self.target_chat = target_chat

        self.last_polls: dict[str, list[dict]] = {}
        self.sources: dict[str, BaseSource] = {}

    def register_source(self, name: str, source: BaseSource):
        self.sources[name] = source
        self._load_last_poll(name)

    async def start(self):
        self.scheduler.add_job(self.do_polling, "date", run_date=datetime.now())
        self.scheduler.start()
        await self.bot.polling()

    async def do_polling(self):
        for name, sources in self.sources.items():

            last_poll = self.last_polls.get(name, [])
            indexed_last_poll = index_dict_array(last_poll, sources.index_keys)

            items = sources.fetch()
            indexed_items = index_dict_array(items, sources.index_keys)

            news = [dict(d) for d in indexed_items - indexed_last_poll]

            await self._send_news(name, news)
            self._store_last_poll(name, items)

        self.scheduler.add_job(
            self.do_polling, "date", run_date=datetime.now() + timedelta(seconds=5)
        )

    async def _send_news(self, name, news):
        assert name in self.sources, f"Source {name} not found"

        for new in news:
            text = self.sources[name].format(new)
            await self.bot.send_message(self.target_chat, text)
        pass

    def _store_last_poll(self, name: str, items):
        assert isinstance(name, str) and len(name) > 0, "Invalid name"

        with open(Path(LAST_POLL_DIRECTORY, f"{name}.json"), "w") as f:
            self.last_polls[name] = items
            f.write(json.dumps(self.last_polls[name], indent=4))
        pass

    def _load_last_poll(self, name: str):
        assert isinstance(name, str) and len(name) > 0, "Invalid name"

        try:
            with open(Path(LAST_POLL_DIRECTORY, f"{name}.json"), "r") as f:
                self.last_polls[name] = json.load(f)
        except FileNotFoundError:
            self.last_polls[name] = []
