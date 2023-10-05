import os
import logging
import arrow
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

load_dotenv()
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers /start and explains the functionality of the bot"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="PulseRome started. Type /new to add an event, /manual to add a manual event and /delete to delete an event",
    )

# /help command to explain the bot
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers /help and explains the functionality of the bot"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Use the command /new to add an event sending a link or a screenshot, /manual to manually add an event and /delete to delete an event",
        parse_mode="Markdown",
    )

if __name__ == "__main__":
    logger = logging.getLogger("mannaggia")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(filename)s | %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    fh = logging.FileHandler('app.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    

    logger.addHandler(ch)
    logger.addHandler(fh)

    application = ApplicationBuilder().token(TG_TOKEN).build()

    new_conversation_handler = create_new_conv_handler()

    manual_conversation_handler = create_manual_conv_handler()

    delete_conv_handler = delete_conv()

    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)
    application.add_handler(start_handler)
    application.add_handler(new_conversation_handler)
    application.add_handler(manual_conversation_handler)
    application.add_handler(delete_conv_handler)

    application.run_polling()
