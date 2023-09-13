import logging
import os
import io
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
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from dotenv import load_dotenv

from scrape_rome.openai import get_event_info
from scrape_rome import db_handling
from scrape_rome.ig import return_username_caption


load_dotenv()

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPEN_AI_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers /start and explains the functionality of the bot"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="PulseRome started. Type /new to add an event",
    )

#TODO: maybe fix this shit code
async def manual_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks about the kind of content youre sending"""
    logger.info('wooo')
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

Start by sending me the name of the event
    """
    await update.message.reply_text(msg, parse_mode="Markdown")

    return MANUAL_START

async def manual_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['event']['name'] = text
    await update.message.reply_text("Send me the date in format YYYY-MM-DD HH:MM:SS")
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

async def manual_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['event']['link'] = text


    response = context.user_data['event']
    msg = f"""
*Name:* {response["name"]}
*Date:* {response["date"]}
*Artists:* {response["artists"]}
*Organizer:* {response["organizer"]}
*Location:* {response["location"]}
*Price:* {response["price"]}
*Link:* {response["link"]}
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

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks about the kind of content youre sending"""
    reply_keyboard = [
        ["IG LINK", "FB LINK", "IG SCREEN", "FB SCREEN"]
    ]

    await update.message.reply_text(
        "What content are you sending?",
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
            response = result if description else "Sorry, couldn't extract any caption from the post."
            context.user_data['event'] = response
        elif 'facebook.com' in text:
            response = "Sorry, I can't handle facebook links yet."
        else:
            response = "Sorry, I can't understand you. Use the command /help to see what I can do."   
    else:
        response = f'Couldn\'t parse your message.\nThis is your last recorded message: {update.message.text}.\nThis is the type of content you selected: {TYPE_OF_CONTENT}'
    
    response = context.user_data['event']
    msg = f"""
*Name:* {response["name"]}
*Date:* {response["date"]}
*Artists:* {response["artists"]}
*Organizer:* {response["organizer"]}
*Location:* {response["location"]}
*Price:* {response["price"]}
*Link:* {response["link"]}
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
            # care, event dates have to be strings
            duplicated = db_handling.insert_event_if_no_similar(connection, event)
            if duplicated:
                await query.edit_message_text(f"This event is too similar to {duplicated[0]} by {duplicated[1]} happening on same date, won't be added.")
            else:
                await query.edit_message_text("Ok adding to database!")

        return ConversationHandler.END
    else:
        reply_keyboard = [
        ["NAME", "DATE", "ARTISTS", "ORGANIZER","LOCATION","PRICE","LINK"]]

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

SELECTED_CONTENT, ASKED_FOR_CONTENT, CREATED_EVENT, ASKED_IF_CORRECT, SELECTED_PARAMETER_TO_CORRECT, ASKED_FOR_CORRECTION = range(6)
MANUAL_START,MANUAL_NAME,MANUAL_DATE,MANUAL_ARTISTS,MANUAL_ORGANIZER,MANUAL_PRICE,MANUAL_LINK = range(6, 13)

if __name__ == "__main__":
    application = ApplicationBuilder().token(TG_TOKEN).build()

    new_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("new", new)],
        states={
            SELECTED_CONTENT: [
                MessageHandler(filters.Regex("^(IG LINK|FB LINK|IG SCREEN|FB SCREEN)$"), sendme)],
            ASKED_FOR_CONTENT: [MessageHandler(filters.TEXT | filters.PHOTO, answer)],
            CREATED_EVENT: [CallbackQueryHandler(save_or_correct)],
            SELECTED_PARAMETER_TO_CORRECT: [MessageHandler(filters.Regex(
                        "^(NAME|DATE|ARTISTS|ORGANIZER|LOCATION|PRICE|LINK)$"), ask_correction)],
            ASKED_FOR_CORRECTION: [MessageHandler(filters.TEXT, correct)],
        },
        fallbacks=[],
    )

    manual_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("manual", manual_start)],
        states={
            MANUAL_START: [MessageHandler(filters.TEXT, manual_name)],
            MANUAL_NAME: [MessageHandler(filters.TEXT, manual_date)],
            MANUAL_DATE: [MessageHandler(filters.TEXT, manual_artists)],
            MANUAL_ARTISTS: [MessageHandler(filters.TEXT, manual_organizer)],
            MANUAL_ORGANIZER: [MessageHandler(filters.TEXT, manual_price)],
            MANUAL_PRICE: [MessageHandler(filters.TEXT, manual_link)],
            MANUAL_LINK: [MessageHandler(filters.TEXT, manual_end)],
            CREATED_EVENT: [CallbackQueryHandler(save_or_correct)],
            SELECTED_PARAMETER_TO_CORRECT: [MessageHandler(filters.Regex(
                        "^(NAME|DATE|ARTISTS|ORGANIZER|LOCATION|PRICE|LINK)$"), ask_correction)],
            ASKED_FOR_CORRECTION: [MessageHandler(filters.TEXT, correct)]
        },
        fallbacks=[],
    )

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)
    application.add_handler(new_conversation_handler)
    application.add_handler(manual_conversation_handler)

    application.run_polling()
