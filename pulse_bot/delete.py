import sqlite3

from telegram import (
    Update,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

from scrape_rome.custom_logger import logger
from scrape_rome import db_handling,html_page
from .general import cancel

ASKED_WHICH_EVENT = 15

async def ask_which_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    await update.message.reply_text("Copy paste from the pulse site which event you want deleted. /cancel to cancel")
    return ASKED_WHICH_EVENT

async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    organizer, name = text.split(" || ")
    with sqlite3.connect('pulse.db') as connection:
        deleted = db_handling.delete_row_by_name_and_organizer(connection,name,organizer)
    if deleted >= 0:
        user = update.message.from_user
        logger.info(f'User {user["username"]} deleted event {name} by {organizer}')
        html_page.update_webpage(connection,"www/gen_index.html")
        await update.message.reply_text("Deleted the event.")
    else:
        await update.message.reply_text("Couldn't find any event like that. Try /delete again.")
    return ConversationHandler.END

def delete_conv():
    return ConversationHandler(
        entry_points=[CommandHandler("delete", ask_which_event)],
        states={
            ASKED_WHICH_EVENT: [MessageHandler(filters.TEXT & (~ filters.COMMAND), delete_event)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )