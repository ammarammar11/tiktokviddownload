import os

import dotenv
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
)

from handlers import roll, handle_message, choose, handle_all
from logger import logger

dotenv.load_dotenv()


def main() -> None:
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("choose", choose))
    app.add_handler(CommandHandler("ch", choose))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_handler(CommandHandler("/all", handle_all))
    app.add_handler(MessageHandler(filters.Regex(r'(?i)@all'), handle_all))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
