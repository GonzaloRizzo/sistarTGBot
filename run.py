from tg_bank_forwarder.bot import TGBankForwarderBot
from dotenv import load_dotenv
from rich import inspect

load_dotenv()
bot = TGBankForwarderBot("config.yml")
# inspect(bot.check_accounts())
# bot.loop()

bot.check_accounts()