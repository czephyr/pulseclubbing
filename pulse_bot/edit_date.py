import sqlite3
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from datetime import datetime
from dateutil.relativedelta import relativedelta
from scrape_rome import db_handling, html_page
from .utils import restricted
from .general import cancel

logger = logging.getLogger("mannaggia")

ASKED_FOR_NEW_DATE, RECEIVING_NEW_DATE = 17, 18

@restricted
async def ask_event_name_for_date_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks for the name of the event to change the date."""
    await update.message.reply_text("Please enter the name of the event you want to change the date for. /cancel to cancel")
    logging.info(f"User {update.message.from_user['username']} asked to change the date of an event")
    return ASKED_FOR_NEW_DATE

async def ask_for_new_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores event name and asks for the new date."""
    context.user_data['event_name_to_edit'] = update.message.text
    await update.message.reply_text("Please enter the new date for the event in YYYY-MM-DD HH:MM:SS format.")
    return RECEIVING_NEW_DATE

async def update_event_date_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Updates the event's date in the database."""
    new_date_str = update.message.text
    event_info = context.user_data.pop('event_name_to_edit', None)
    organizer, event_name = event_info.split(" || ")
    
    try:
        # Validate and format the new date
        new_date = datetime.strptime(new_date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD HH:MM:SS format.")
        return RECEIVING_NEW_DATE
    
    if organizer and event_name:
        with sqlite3.connect('pulse.db') as connection:
            updated = db_handling.update_event_date(connection, event_name, organizer, new_date.strftime("%Y-%m-%d %H:%M:%S"))
            
            if updated:
                await update.message.reply_text("Event date updated successfully.")
            else:
                await update.message.reply_text("Could not find the event or update failed.")
    else:
        await update.message.reply_text("Event information was not provided correctly. Please start over.")
    return ConversationHandler.END

def edit_date_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("edit_date", ask_event_name_for_date_change)],
        states={
            ASKED_FOR_NEW_DATE: [MessageHandler(filters.TEXT & (~filters.COMMAND), ask_for_new_date)],
            RECEIVING_NEW_DATE: [MessageHandler(filters.TEXT & (~filters.COMMAND), update_event_date_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=600
    )