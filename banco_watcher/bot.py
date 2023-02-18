from datetime import datetime, timedelta
from pydantic import BaseModel, parse_file_as

from telebot.async_telebot import AsyncTeleBot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from banco_watcher.providers.ItauProvider import ItauProvider
from banco_watcher.providers.SistarbancProvider import SistarbancProvider

class BancoWatcherConfig(BaseModel):
    token: str
    target_chat: str
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
        for provider in [*self.config.itau, *self.config.sistarbank]:
            for account in provider.fetch_accounts():
                for entry in account.compare_with_cache():
                    await self.send_entries(entry)
                account.store_cache()
        self.scheduler.add_job(self.do_polling, "date", run_date=datetime.now() + timedelta(minutes=30))
    
    async def send_entries(self, entry):
        await self.bot.send_message(self.config.target_chat, entry.format())


