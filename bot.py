import os
import logging
import locale
from datetime import timedelta, datetime,time
import sqlite3
from collections import defaultdict
from scrape_rome import db_handling,utils
from telegram import (
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from dotenv import load_dotenv
from pulse_bot.utils import restricted, create_tg_post # Decorator to restrict access to certain users
from pulse_bot.new import create_new_conv_handler
from pulse_bot.manual import create_manual_conv_handler
from pulse_bot.delete import delete_conv
from pulse_bot.edit_date import edit_date_conv_handler


load_dotenv()
IS_LOCAL = os.getenv("RUN_LOCALLY") == 'true'
if IS_LOCAL:
    TG_TOKEN = os.getenv("LOCAL_TELEGRAM_TOKEN")
else:
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

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers /start and explains the functionality of the bot"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="PulseRome started. Type /new to add an event, /manual to add a manual event and /delete to delete an event",
    )

@restricted
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers /help and explains the functionality of the bot"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Use the command /new to add an event sending a link or a screenshot, /manual to manually add an event and /delete to delete an event",
        parse_mode="Markdown",
    )

async def callback_minute(context: ContextTypes.DEFAULT_TYPE):
    locale.setlocale(locale.LC_TIME, 'it_IT')
    with sqlite3.connect('pulse.db') as db_connection:
        events_in_db = db_handling.return_valid_events_by_date(db_connection, datetime.now(), datetime.now() + timedelta(days=3))
    msg = "Here are some events: \n"
    
    modified_events = []

    for event in events_in_db:
        # Convert the date string at event[2] to a date object and back to a string
        new_date = datetime.strptime(event[2], '%Y-%m-%d %H:%M:%S').date()
        
        # Create a new tuple with the modified date and add it to the modified_events list
        # This example assumes your tuple has 5 elements (indexed from 0 to 4)
        # Adjust the tuple creation as per your actual data structure
        modified_event = (event[0], event[1], new_date, event[4], event[7])
        modified_events.append(modified_event)

    # sort events by date
    sorted_events = sorted(modified_events, key=lambda event: event[2])

    # Group events by date
    events_by_date = defaultdict(list)
    for event in sorted_events:
        events_by_date[event[2]].append(event)

    for date, events in events_by_date.items():
        msg += f"{date.strftime('%A %d %B')}:\n"
        for event in events:
            msg += f"- {event[1]} @ **{event[3]}**: [link]({event[4]})\n"
        msg+="\n"
    
    msg+="\npiu' avanti? Li trovi su [stase.it](stase.it)"
    await context.bot.send_message(chat_id="-1002041332676",text=msg, parse_mode="Markdown")
    print(msg)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)


if __name__ == "__main__":
    application = ApplicationBuilder().token(TG_TOKEN).build()
    job_queue = application.job_queue

    # at 14:00UTC+2 on friday
    job_minute = job_queue.run_daily(callback_minute, time(hour=12, minute=5, second=0), days=[5])

    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)
    new_conversation_handler = create_new_conv_handler()
    manual_conversation_handler = create_manual_conv_handler()
    delete_conv_handler = delete_conv()
    edit_date_handler = edit_date_conv_handler()

    application.add_handler(start_handler)
    application.add_handler(new_conversation_handler)
    application.add_handler(manual_conversation_handler)
    application.add_handler(delete_conv_handler)
    application.add_handler(edit_date_handler)
    application.add_error_handler(error_handler)

    application.run_polling()
