from dotenv import load_dotenv

from tg_bank_forwarder.bot import TGBankForwarderBot

load_dotenv()
bot = TGBankForwarderBot("config.yml")
# inspect(bot.check_accounts())
# bot.loop()

bot.check_accounts()
