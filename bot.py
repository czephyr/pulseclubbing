import os
import logging
from telegram import (
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from dotenv import load_dotenv
from pulse_bot.new import create_new_conv_handler
from pulse_bot.manual import create_manual_conv_handler
from pulse_bot.delete import delete_conv

for name, logger in logging.root.manager.loggerDict.items():
    logger.disabled=True

load_dotenv()
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers /start and explains the functionality of the bot"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="PulseRome started. Type /new to add an event, /manual to add a manual event",
    )

if __name__ == "__main__":

    application = ApplicationBuilder().token(TG_TOKEN).build()

    new_conversation_handler = create_new_conv_handler()

    manual_conversation_handler = create_manual_conv_handler()

    delete_conv_handler = delete_conv()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)
    application.add_handler(new_conversation_handler)
    application.add_handler(manual_conversation_handler)
    application.add_handler(delete_conv_handler)

    application.run_polling()
