from datetime import datetime, timedelta
from pydantic import BaseModel, parse_file_as
import sentry_sdk

from telebot.async_telebot import AsyncTeleBot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from banco_watcher.providers.ItauProvider import ItauProvider
from banco_watcher.providers.SistarbancProvider import SistarbancProvider

# BUG: Looks like sometimes itau misses `descripcionAdicional` and the hash changes
# > diff 2024-02-01T04:19_itau:itau:4d921396e8894d1f4d783585cc77cc5d1d45c27e1c381f66f379643ec2f57be8.json 2024-02-01T04:50_itau:itau:4d921396e8894d1f4d783585cc77cc5d1d45c27e1c381f66f379643ec2f57be8.json
# Looks like my as_touple and inserting everything into a set might not be working properly.

class BancoWatcherConfig(BaseModel):
    token: str
    target_chat: str
    # TODO: Have sentry_dsn defined here

    # TODO: Have a single Provider array using pydantic discriminators
    itau: list[ItauProvider]
    sistarbank: list[SistarbancProvider]

class BancoWatcherBot:
    def __init__(self, config_file):
        self.scheduler = AsyncIOScheduler()
        self.config = parse_file_as(BancoWatcherConfig, config_file)
        self.bot = AsyncTeleBot(self.config.token, parse_mode="HTML")
    
    async def start(self):
        self.scheduler.add_job(self.do_polling, "date", run_date=datetime.now())
        self.scheduler.start()
        await self.bot.polling(non_stop=True)

    async def do_polling(self):
        providers: list[ItauProvider | SistarbancProvider] = [*self.config.itau, *self.config.sistarbank]
        for provider in providers:
            try:
                for title, entry_list in provider.fetch_accounts():
                    new_entries, missing_entries = entry_list.compare_with_cache()

                    for entry in new_entries:
                        await self.send_entry(title, entry)

                    if len(new_entries) > 0 or len(missing_entries) > 0:
                        print(f"new_entries: {len(new_entries)}")
                        print(f"missing_entries: {len(missing_entries)}")
                        entry_list.store_cache()
            except Exception as err:
                print(err)
                sentry_sdk.capture_exception(err)
                await self.bot.send_message(self.config.target_chat, str(err))
                raise err
        self.scheduler.add_job(self.do_polling, "date", run_date=datetime.now() + timedelta(minutes=30))
    
    async def send_entry(self, title, entry):
        text = f"<u>{title}</u>\n" 
        text += "\n"
        text += entry.format()
        await self.bot.send_message(self.config.target_chat, text)


