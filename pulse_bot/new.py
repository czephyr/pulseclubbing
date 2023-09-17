import io
import os
import json
import sqlite3

from PIL import Image
import pytesseract

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

from scrape_rome.openai import get_event_info
from scrape_rome import db_handling
from scrape_rome.ig import return_username_caption
from scrape_rome.custom_logger import logger
from .general import cancel


OPEN_AI_KEY = os.getenv("OPENAI_API_KEY")

SELECTED_CONTENT, ASKED_FOR_CONTENT, CREATED_EVENT, ASKED_IF_CORRECT, SELECTED_PARAMETER_TO_CORRECT, ASKED_FOR_CORRECTION = range(6)

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks about the kind of content youre sending"""
    reply_keyboard = [
        ["IG LINK", "FB LINK", "IG SCREEN", "FB SCREEN"]
    ]
    user = update.message.from_user
    logger.info(f'User {user["username"]} requested new event adding')


    await update.message.reply_text(
        "What content are you sending? /cancel to cancel",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Type of content to select:",
        ),
    )

    return SELECTED_CONTENT


async def sendme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['type_of_content'] = text.lower()
    if "link" in text.lower():
        await update.message.reply_text("Send me the link",reply_markup=ReplyKeyboardRemove())
    elif "screen" in text.lower():
        await update.message.reply_text("Send me the screenshot",reply_markup=ReplyKeyboardRemove())
    return ASKED_FOR_CONTENT



async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Produces the result on the content provided. 
    On images does OCR and openai call, on links scrapes and openai call.
    Then asks if the produced JSON is correct."""
    
    if "screen" in context.user_data['type_of_content']:
        #find a way not to save this shit?
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        io_stream = io.BytesIO(b"")
        await file.download_to_memory(io_stream)
        extracted_text = pytesseract.image_to_string(Image.open(io_stream))
        username, description = extracted_text.split(" ", 1)
        response = json.loads(get_event_info(description, source='instagram', key=OPEN_AI_KEY))
        context.user_data['event'] = response
    elif "link" in context.user_data['type_of_content']:
        text = update.message.text
        if 'instagram.com' in text:
            description, username = return_username_caption(text)
            result = json.loads(get_event_info(description, source='instagram', key=OPEN_AI_KEY, username=username, link=text))
            result["raw_descr"] = description
            context.user_data['event'] = response
        elif 'facebook.com' in text:
            response = "Sorry, I can't handle facebook links yet."
        else:
            response = "Sorry, I can't understand you. Use the command /help to see what I can do."   
    else:
        response = f'Couldn\'t parse your message.\nThis is your last recorded message: {update.message.text}.\n'
    
    response = context.user_data['event']
    msg = f"""
*Name:* {response["name"]}
*Date:* {response["date"]}
*Artists:* {response["artists"]}
*Organizer:* {response["organizer"]}
*Location:* {response["location"]}
*Price:* {response["price"]}
*Link:* {response["link"]}
*Raw_descr:* {response["raw_descr"]}
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

async def save_or_correct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """If the user pressed the Yes button, the JSON is deemed correct and we save it to database 
    and close the conversation.
    If the user pressed the No button then prompts the user for a correct version of the JSON"""
    query = update.callback_query
    await query.answer()
    logger.info(query.data)
    if query.data == "yes":
        response = context.user_data['event']
        event = (response["name"],response["date"],response["artists"],response["organizer"],response["location"],response["price"],response["link"])
        with sqlite3.connect('pulse.db') as connection:
            user = update.callback_query.from_user
            logger.info(f'User {user["username"]} inserting event {event[0]} by {event[3]} on date {event[1]}')
            # care, event dates have to be strings
            duplicated = db_handling.insert_event_if_no_similar(connection, event)
            if duplicated:
                await query.edit_message_text(f"This event is too similar to {duplicated[0]} by {duplicated[1]} happening on same date, won't be added.")
            else:
                await query.edit_message_text("Ok adding to database!")

        return ConversationHandler.END
    else:
        reply_keyboard = [
        ["NAME", "DATE", "ARTISTS", "ORGANIZER","LOCATION","PRICE","LINK","RAW_DESCR"]]

        await query.message.reply_text(
            "What do you want to correct?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,
                input_field_placeholder="Select data to correct:",
            ),
        )

        return SELECTED_PARAMETER_TO_CORRECT
    

async def ask_correction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    context.user_data['to_correct'] = update.message.text.lower()
    logger.info(f"Asked to correct: {context.user_data['to_correct']}")
    await update.message.reply_text("Send me your correction:",reply_markup=ReplyKeyboardRemove())
    return ASKED_FOR_CORRECTION

async def correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    parameter_to_correct = context.user_data['to_correct']
    logger.info(f"Correcting: {parameter_to_correct}")
    context.user_data['event'][parameter_to_correct] = update.message.text


    response = context.user_data['event']
    msg = f"""
*Name:* {response["name"]}
*Date:* {response["date"]}
*Artists:* {response["artists"]}
*Organizer:* {response["organizer"]}
*Location:* {response["location"]}
*Price:* {response["price"]}
*Link:* {response["link"]}
*Raw_descr:* {response["raw_descr"]}
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

def create_new_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("new", new)],
        states={
            SELECTED_CONTENT: [
                MessageHandler(filters.Regex("^(IG LINK|FB LINK|IG SCREEN|FB SCREEN)$"), sendme)],
            ASKED_FOR_CONTENT: [MessageHandler(filters.TEXT | filters.PHOTO & (~ filters.COMMAND), answer)],
            CREATED_EVENT: [CallbackQueryHandler(save_or_correct)],
            SELECTED_PARAMETER_TO_CORRECT: [MessageHandler(filters.Regex(
                        "^(NAME|DATE|ARTISTS|ORGANIZER|LOCATION|PRICE|LINK|RAW_DESCR)$"), ask_correction)],
            ASKED_FOR_CORRECTION: [MessageHandler(filters.TEXT & (~ filters.COMMAND), correct)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )