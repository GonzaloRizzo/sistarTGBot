import json
import logging
from typing import Callable, Generator, Tuple, Type, TypeVar

from rich import print
from pathlib import Path
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telebot.async_telebot import AsyncTeleBot

from tg_bank_forwarder.sources.base import BaseSourceModel, BaseSourceModelList

log = logging.getLogger(__name__)

LAST_POLL_DIRECTORY = "last_polls"


T = TypeVar("T", bound=BaseSourceModel)
SourceFnYield = Tuple[str, list[T], Type[T], str]
SourceFn = Callable[[], Generator[SourceFnYield, None, None]]
FormatterFn = Callable[[dict], str]


class TelegramBot:
    def __init__(self, token, target_chat) -> None:
        self.scheduler = AsyncIOScheduler()

        self.bot = AsyncTeleBot(token, parse_mode="HTML")
        self.target_chat = target_chat

        self.last_polls: dict[str, list[dict]] = {}
        self.sources: list[SourceFn] = []

    def register_source(self, source: SourceFn):
        self.sources.append(source)

    async def start(self):
        self.scheduler.add_job(self.do_polling, "date", run_date=datetime.now())
        self.scheduler.start()
        await self.bot.polling()

    async def do_polling(self):
        for sourceFn in self.sources:
            log.info(f"Polling {sourceFn.__name__}")

            for account_name, items, Model, title in sourceFn():
                print(f"Found {len(items)} items in {account_name}")

                last_poll_indexed = {
                    Model.parse_obj(obj).to_index()
                    for obj in self._load_last_poll(account_name)
                }

                items_indexed = {obj.to_index() for obj in items}

                new_indexes = items_indexed - last_poll_indexed

                news = [i for i in items if i.to_index() in new_indexes]

                log.info(f"Found {len(news)} new item(s)")

                await self._send_news(news, title)
                self._store_last_poll(account_name, items)

        run_date = datetime.now() + timedelta(minutes=30)
        print(f"Next run at {run_date}")
        self.scheduler.add_job(self.do_polling, "date", run_date=run_date)

    async def _send_news(self, news: list[T], title: str):
        for new in news:
            text = f"<b><u>{title}</u></b>\n\n"
            text += new.format()
            await self.bot.send_message(self.target_chat, text)
        pass

    def _store_last_poll(self, name: str, items):
        assert isinstance(name, str) and len(name) > 0, "Invalid name"

        with open(Path(LAST_POLL_DIRECTORY, f"{name}.json"), "w") as f:
            self.last_polls[name] = items
            f.write(
                BaseSourceModelList.parse_obj(items).json(indent=4, exclude_unset=True)
            )
        pass

    def _load_last_poll(self, account_name: str):
        assert (
            isinstance(account_name, str) and len(account_name) > 0
        ), "Invalid account name"

        if account_name not in self.last_polls:
            try:
                with open(Path(LAST_POLL_DIRECTORY, f"{account_name}.json"), "r") as f:
                    self.last_polls[account_name] = json.load(f)
            except FileNotFoundError:
                self.last_polls[account_name] = []

        return self.last_polls[account_name]
