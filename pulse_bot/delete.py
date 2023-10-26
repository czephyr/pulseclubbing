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
from scrape_rome import db_handling,html_page
from .general import cancel

logger = logging.getLogger("mannaggia")

ASKED_WHICH_EVENT, ASKED_IF_WAS_TECHNO = 15,16

async def ask_which_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks to copy the event from the site"""
    await update.message.reply_text("Copy paste from the pulse site which event you want deleted. /cancel to cancel")
    return ASKED_WHICH_EVENT

async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    organizer, name = text.split(" || ")
    with sqlite3.connect('pulse.db') as connection:
        deleted = db_handling.delete_row_by_name_and_organizer(connection,name,organizer)
    if deleted:
        context.user_data['id_event_to_delete'] = deleted 
        user = update.message.from_user
        logger.info(f'User {user["username"]} deleted event {name} by {organizer}')
        html_page.update_webpage(connection,"www/gen_index.html",datetime.today())
        html_page.update_webpage(connection,"www/next_month.html",datetime.today()+relativedelta(months=1))
        await update.message.reply_text("Deleted the event.")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Yes", callback_data="yes"),
                    InlineKeyboardButton("No", callback_data="no"),
                ]
            ]
        )
        await update.message.reply_text("Was it a clubbing event?", reply_markup=keyboard)
        return ASKED_IF_WAS_TECHNO
    else:
        await update.message.reply_text("Couldn't find any event like that. Try /delete again.")
        return ConversationHandler.END

async def was_it_clubbing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """If the user pressed the Yes button, the JSON is deemed correct and we save it to database 
    and close the conversation.
    If the user pressed the No button then prompts the user for a correct version of the JSON"""
    query = update.callback_query
    await query.answer()
    event_id = context.user_data['id_event_to_delete']
    context.user_data.pop('id_event_to_delete')
    with sqlite3.connect('pulse.db') as connection:
        if query.data == "yes":
            is_clubbing = 1
        else:
            is_clubbing = 0
        updated = db_handling.update_is_clubbing(connection, event_id,is_clubbing)

        if updated:
            await query.edit_message_text("Ok, ty.")
        else:
            await query.edit_message_text("Wtf no event with that id")
    return ConversationHandler.END

def delete_conv():
    return ConversationHandler(
        entry_points=[CommandHandler("delete", ask_which_event)],
        states={
            ASKED_WHICH_EVENT: [MessageHandler(filters.TEXT & (~ filters.COMMAND), delete_event)],
            ASKED_IF_WAS_TECHNO: [CallbackQueryHandler(was_it_clubbing)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],conversation_timeout=600
    )