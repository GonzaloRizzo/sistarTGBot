import logging
from dotenv import load_dotenv
from os import getenv
from TelegramBot import TelegramBot

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

if __name__ == "__main__":
    target_chat = getenv("TG_TARGET_CHAT")
    token = getenv("TG_TOKEN")

    s = TelegramBot(token, target_chat)
    s.run()
