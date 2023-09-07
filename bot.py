#TODO: implement user specific data that gets passed through the handlers (JSON of the event sent by the user)
# https://stackoverflow.com/questions/61053602/python-telegram-bot-pass-argument-between-conversation-handlers

import logging
import os
import json

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
from scrape_rome.ig import post_handler


load_dotenv()

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPEN_AI_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


NEW, CONTENT, ANSWER, INCORRECT = range(4)

TYPE_OF_CONTENT = ""


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

    return NEW


async def sendme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and propts for the content"""
    text = update.message.text
    context.user_data['type_of_content'] = text.lower()
    if "link" in text.lower():
        await update.message.reply_text("Send me the link")
    elif "screen" in text.lower():
        await update.message.reply_text("Send me the screenshot")
    return CONTENT


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
    elif "link" in context.user_data['type_of_content']:
        text = update.message.text
        if 'instagram.com' in text:
            description, username = post_handler(text)
            result = json.loads(get_event_info(description, source='instagram', key=OPEN_AI_KEY, username=username, link=text))
            response = result if description else "Sorry, couldn't extract any caption from the post."
        elif 'facebook.com' in text:
            response = "Sorry, I can't handle facebook links yet."
        else:
            response = "Sorry, I can't understand you. Use the command /help to see what I can do."   
    else:
        response = f'Couldn\'t parse your message.\nThis is your last recorded message: {update.message.text}.\nThis is the type of content you selected: {TYPE_OF_CONTENT}'
    await update.message.reply_text(f"```\n {response} \n```", parse_mode="Markdown")
    # await update.message.reply_text(TYPE_OF_CONTENT if TYPE_OF_CONTENT else f'THIS IS THE DEFAULT RESPONSE {response + update.message.text}')
    
    # need to insert the json in context.user_data so that next handler can access json
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Yes", callback_data="yes"),
                InlineKeyboardButton("No", callback_data="no"),
            ]
        ]
    )
    await update.message.reply_text("is this correct?", reply_markup=keyboard)

    return ANSWER


async def correctness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """If the user pressed the Yes button, the JSON is deemed correct and we save it to database 
    and close the conversation.
    If the user pressed the No button then prompts the user for a correct version of the JSON"""
    query = update.callback_query
    query.answer()
    logger.info(query.data)
    if query.data == "yes":
        await query.edit_message_text("Ok adding to database!")
        # add to database here
        # needs to search context.user_data to have access to JSON from previous handler
        return ConversationHandler.END
    else:
        await query.edit_message_text("That sucks, please send a correct version")
        return INCORRECT


async def insert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Executes after the user has sent a corrected JSON, saves the JSON to db."""
    text = update.message.text
    # insert to db
    await update.message.reply_text("added to database!")
    return ConversationHandler.END


if __name__ == "__main__":
    application = ApplicationBuilder().token(TG_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("new", new)],
        states={
            NEW: [
                MessageHandler(
                    filters.Regex(
                        "^(IG LINK|FB LINK|IG SCREEN|FB SCREEN)$"
                    ),
                    sendme,
                )
            ],
            CONTENT: [MessageHandler(filters.TEXT | filters.PHOTO, answer)],
            ANSWER: [CallbackQueryHandler(correctness)],
            INCORRECT: [MessageHandler(filters.TEXT, insert)],
        },
        fallbacks=[],
    )

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)
    application.add_handler(conversation_handler)

    application.run_polling()
