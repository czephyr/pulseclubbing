import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.helpers import (
    escape_markdown
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from .utils import restricted
from .general import cancel
from .new import save_or_correct, ask_correction, correct, CREATED_EVENT, SELECTED_PARAMETER_TO_CORRECT, ASKED_FOR_CORRECTION

logger = logging.getLogger("mannaggia")

MANUAL_START,MANUAL_NAME,MANUAL_DATE,MANUAL_ARTISTS,MANUAL_ORGANIZER,MANUAL_PRICE,MANUAL_LINK,MANUAL_DESCR = range(6, 14)

#TODO: maybe fix this shit code
@restricted
async def manual_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks about the kind of content youre sending"""
    user = update.message.from_user
    logger.info(f'User {user["username"]} requested manual event adding')
    context.user_data['event'] = {}
    msg ="""
This is the structure of the event data

*Name:* 
*Date:*
*Artists:*
*Organizer:*
*Location:*
*Price:*
*Link:*

Start by sending me the name of the event, 
/cancel to cancel
    """
    await update.message.reply_text(msg, parse_mode="Markdown")

    return MANUAL_START

async def manual_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['event']['name'] = text
    await update.message.reply_text("Send me the date in format YYYY-MM-DD HH:mm:ss")
    return MANUAL_NAME

async def manual_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['event']['date'] = text
    await update.message.reply_text("Send me the artists separated by a comma")
    return MANUAL_DATE

async def manual_artists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['event']['artists'] = text
    await update.message.reply_text("Send me the organizer")
    return MANUAL_ARTISTS

async def manual_organizer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['event']['organizer'] = text
    await update.message.reply_text("Send me the Location")
    return MANUAL_ORGANIZER

async def manual_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['event']['location'] = text
    await update.message.reply_text("Send me the price, if its free send 0, if its unknown send -1")
    return MANUAL_PRICE

async def manual_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['event']['price'] = text
    await update.message.reply_text("Send me the link to the event")
    return MANUAL_LINK

async def manual_rawdescr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['event']['link'] = text
    await update.message.reply_text("Send me the raw description of the event")
    return MANUAL_DESCR

async def manual_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['event']['raw_descr'] = text


    response = context.user_data['event']
    msg = f"""
*Name:* {escape_markdown(response["name"])}
*Date:* {escape_markdown(response["date"])}
*Artists:* {escape_markdown(response["artists"])}
*Organizer:* {escape_markdown(response["organizer"])}
*Location:* {escape_markdown(response["location"])}
*Price:* {escape_markdown(response["price"])}
*Link:* {escape_markdown(response["link"])}
*Raw_descr:* {escape_markdown(response["raw_descr"])}
    """
    await update.message.reply_text(msg, parse_mode="Markdown")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Yes", callback_data="yes"),
                InlineKeyboardButton("No", callback_data="no"),
            ]
        ]
    )
    await update.message.reply_text("is this correct?", reply_markup=keyboard)
    return CREATED_EVENT


def create_manual_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("manual", manual_start)],
        states={
            MANUAL_START: [MessageHandler(filters.TEXT & (~filters.COMMAND), manual_name)],
            MANUAL_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), manual_date)],
            MANUAL_DATE: [MessageHandler(filters.TEXT & (~filters.COMMAND), manual_artists)],
            MANUAL_ARTISTS: [MessageHandler(filters.TEXT & (~filters.COMMAND), manual_organizer)],
            MANUAL_ORGANIZER: [MessageHandler(filters.TEXT & (~filters.COMMAND), manual_price)],
            MANUAL_PRICE: [MessageHandler(filters.TEXT & (~filters.COMMAND), manual_link)],
            MANUAL_LINK: [MessageHandler(filters.TEXT & (~filters.COMMAND), manual_rawdescr)],
            MANUAL_DESCR: [MessageHandler(filters.TEXT & (~filters.COMMAND), manual_end)],
            CREATED_EVENT: [CallbackQueryHandler(save_or_correct)],
            SELECTED_PARAMETER_TO_CORRECT: [MessageHandler(filters.Regex(
                        "^(NAME|DATE|ARTISTS|ORGANIZER|LOCATION|PRICE|LINK|RAW_DESCR)$"), ask_correction)],
            ASKED_FOR_CORRECTION: [MessageHandler(filters.TEXT & (~filters.COMMAND), correct)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],conversation_timeout=600
    )