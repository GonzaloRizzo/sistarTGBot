import json
import logging

from rich import print
from pathlib import Path
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telebot.async_telebot import AsyncTeleBot

from tg_bank_forwarder.sources.base import BaseSource

log = logging.getLogger(__name__)

LAST_POLL_DIRECTORY = "last_polls"


def index_dict_array(array, index_keys):
    return dict(
        (frozenset((k, v) for k, v in d.items() if k in index_keys), d) for d in array
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
        for name, source in self.sources.items():
            log.info(f"Polling {name}")

            last_poll = self.last_polls.get(name, [])
            indexed_last_poll = index_dict_array(last_poll, source.index_keys)

            items = source.fetch()
            print(items)
            indexed_items = index_dict_array(items, source.index_keys)

            print(indexed_items)

            news = [
                v
                for k, v in indexed_items.items()
                if k in indexed_items.keys() - indexed_last_poll.keys()
            ]

            log.info(f"Found {len(news)} new(s)")

            print(news)

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
