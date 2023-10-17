import os
import logging
from datetime import timedelta, datetime
import sqlite3
from scrape_rome import db_handling
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

async def callback_minute(context: ContextTypes.DEFAULT_TYPE):
    with sqlite3.connect('pulse.db') as connection:
        days = db_handling.visits_stats(connection)
    msg = "Here are the visit counts from the past week \n"
    for day,count in days:
        msg += f"*{day} {datetime.strptime(day, '%Y-%m-%d').weekday()}*: {count}\n"
    await context.bot.send_message(chat_id=474799562, text=msg, parse_mode="Markdown",)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)

if __name__ == "__main__":
    application = ApplicationBuilder().token(TG_TOKEN).build()
    job_queue = application.job_queue

    job_minute = job_queue.run_repeating(callback_minute, interval=timedelta(days=7), first=datetime.fromisoformat('2011-10-20 23:59:00.000'))

    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)
    new_conversation_handler = create_new_conv_handler()
    manual_conversation_handler = create_manual_conv_handler()
    delete_conv_handler = delete_conv()

    application.add_handler(start_handler)
    application.add_handler(new_conversation_handler)
    application.add_handler(manual_conversation_handler)
    application.add_handler(delete_conv_handler)
    application.add_error_handler(error_handler)

    application.run_polling()
