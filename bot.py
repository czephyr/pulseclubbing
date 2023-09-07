#TODO: implement user specific data that gets passed through the handlers (JSON of the event sent by the user)
# https://stackoverflow.com/questions/61053602/python-telegram-bot-pass-argument-between-conversation-handlers

import logging
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
from scrape_rome.ig import post_handler


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
        await update.message.reply_text("Send me the link")
    elif "screen" in text.lower():
        await update.message.reply_text("Send me the screenshot")
    return ASKED_FOR_CONTENT



async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Produces the result on the content provided. 
    On images does OCR and openai call, on links scrapes and openai call.
    Then asks if the produced JSON is correct."""
    logger.info('Type of content sent by user: %s', context.user_data['type_of_content'])
    if "screen" in context.user_data['type_of_content']:
        #find a way not to save this shit?
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        await file.download_to_drive("./image.jpg")
        extracted_text = pytesseract.image_to_string(Image.open("./image.jpg"))
        username, description = extracted_text.split(" ", 1)
        response = json.loads(get_event_info(description, source='instagram', key=OPEN_AI_KEY))
        context.user_data['event'] = response
    elif "link" in context.user_data['type_of_content']:
        text = update.message.text
        if 'instagram.com' in text:
            logger.info('wooo')
            description, username = post_handler(text)
            result = json.loads(get_event_info(description, source='instagram', key=OPEN_AI_KEY, username=username, link=text))
            response = result if description else "Sorry, couldn't extract any caption from the post."
            context.user_data['event'] = response
            logger.info('wooo2')
            return CREATED_EVENT
    #     elif 'facebook.com' in text:
    #         response = "Sorry, I can't handle facebook links yet."
    #     else:
    #         response = "Sorry, I can't understand you. Use the command /help to see what I can do."   
    # else:
    #     response = f'Couldn\'t parse your message.\nThis is your last recorded message: {update.message.text}.\nThis is the type of content you selected: {TYPE_OF_CONTENT}'
    # #await update.message.reply_text(f"```\n {response} \n```", parse_mode="Markdown")
    # # await update.message.reply_text(TYPE_OF_CONTENT if TYPE_OF_CONTENT else f'THIS IS THE DEFAULT RESPONSE {response + update.message.text}')
    
    # return CREATED_EVENT

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info('wooo3')
    # need to insert the json in context.user_data so that next handler can access json
    response = context.user_data['event']
    msg = f"""
        *Name:* {response["name"]}
        *Date:* {response["date"]}\n
        *Artists:* {response["artists"]}\n
        *Organizer:* {response["organizer"]}\n
        *Location:* {response["location"]}\n
        *Price:* {response["price"]}\n
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

    return ASKED_IF_CORRECT


async def save_or_correct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """If the user pressed the Yes button, the JSON is deemed correct and we save it to database 
    and close the conversation.
    If the user pressed the No button then prompts the user for a correct version of the JSON"""
    query = update.callback_query
    query.answer()
    logger.info(query.data)
    if query.data == "yes":
        await query.edit_message_text("Ok adding to database!")
        response = context.user_data['event']
        event = (response["name"],response["date"],response["artists"],response["organizer"],response["location"],response["price"],response["link"])
        with sqlite3.connect('pulse.db') as connection:
            # care, event dates have to be strings
            db_handling.insert_event(connection, event)
        return ConversationHandler.END
    else:
        reply_keyboard = [
        ["Name", "Date", "Artists", "Organizer","Location","Price","Link"]]

        await update.message.reply_text(
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
    context.user_data['to_correct'] = update.message.text
    await update.message.reply_text("Send me your correction:")
    return ASKED_FOR_CORRECTION

async def correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    parameter_to_correct = context.user_data['to_correct']
    context.user_data['event'][parameter_to_correct] = update.message.text
    return CREATED_EVENT

SELECTED_CONTENT, ASKED_FOR_CONTENT, CREATED_EVENT, ASKED_IF_CORRECT, SELECTED_PARAMETER_TO_CORRECT, ASKED_FOR_CORRECTION = range(6)

if __name__ == "__main__":
    application = ApplicationBuilder().token(TG_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("new", new)],
        states={
            SELECTED_CONTENT: [
                MessageHandler(
                    filters.Regex(
                        "^(IG LINK|FB LINK|IG SCREEN|FB SCREEN)$"
                    ),
                    sendme,
                )
            ],
            ASKED_FOR_CONTENT: [MessageHandler(filters.TEXT | filters.PHOTO, answer)],
            CREATED_EVENT: [CallbackQueryHandler(ask)],
            ASKED_IF_CORRECT: [MessageHandler(filters.Regex(
                        "^(NAME|DATE|ARTISTS|ORGANIZER|LOCATION|PRICE|LINK)$"
                    ), save_or_correct)],
            SELECTED_PARAMETER_TO_CORRECT: [MessageHandler(filters.TEXT, ask_correction)],
            ASKED_FOR_CORRECTION: [MessageHandler(filters.TEXT, correct)],
        },
        fallbacks=[],
    )

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)
    application.add_handler(conversation_handler)

    application.run_polling()
