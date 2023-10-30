import io
import os
import sqlite3
import logging

from datetime import datetime
from dateutil.relativedelta import relativedelta

from PIL import Image
import pytesseract

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
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

from scrape_rome.openai import instagram_event
from scrape_rome import db_handling
from scrape_rome import ig
from scrape_rome import dice
from scrape_rome import html_page, utils
from .general import cancel

logger = logging.getLogger("mannaggia")
OPEN_AI_KEY = os.getenv("OPENAI_API_KEY")

SELECTED_CONTENT, ASKED_FOR_CONTENT, CREATED_EVENT, ASKED_IF_CORRECT, SELECTED_PARAMETER_TO_CORRECT, ASKED_FOR_CORRECTION = range(6)

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks about the kind of content youre sending"""
    reply_keyboard = [
        ["IG LINK", "DICE LINK", "SCREEN"]
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
        await update.message.reply_text("Send me the screenshot along with a caption containing the name of the organizer and the link separated by a comma.\nE.g. Fanfulla5/A, www.facebook.com/events/gae651gea31.",reply_markup=ReplyKeyboardRemove())
    return ASKED_FOR_CONTENT



async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Produces the result on the content provided. 
    On images does OCR and openai call, on links scrapes and openai call.
    Then asks if the produced JSON is correct."""
    
    if "screen" in context.user_data['type_of_content']:
        text = update.message.caption
        try: 
            organizer, link = text.split(',')
        except ValueError:
            logger.info(f"Wrong format for caption: {text}")
            await update.message.reply_text("Wrong format for caption, please start again")
            return ConversationHandler.END
        except AttributeError:
            logger.info(f"Wrong format for caption: {text}")
            await update.message.reply_text("Wrong format for caption, please start again")
            return ConversationHandler.END
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        io_stream = io.BytesIO(b"")
        await file.download_to_memory(io_stream)
        extracted_text = pytesseract.image_to_string(Image.open(io_stream))
        response = instagram_event(extracted_text)
        if not response:
            logger.info(f"OpenAI returned an empty response for {text}")
            await update.message.reply_text("OpenAI returned an empty response.")
            return ConversationHandler.END
        event = {"name": response["name"],
                "date": response["date"],
                "artists":response["artists"],
                "organizer":organizer,
                "location":response["location"],
                "price":response["price"],
                "link":link,
                "raw_descr":extracted_text}
        context.user_data['event'] = event

    elif "link" in context.user_data['type_of_content']:
        text = update.message.text
        context.user_data.pop('type_of_content')
        logger.info(f"Link received: {text}")
        if 'instagram.com' in text:
            shortcode = utils.get_insta_shortcode(text)
            end = False
            with sqlite3.connect('pulse.db') as connection:
                if db_handling.is_igpost_shortcode_in_db(connection, shortcode):
                    end = True
            if end:
                logger.info(f"This post has already been scraped: {text}")
                await update.message.reply_text("This post has already been scraped.")
                return ConversationHandler.END
            description, username = ig.return_username_caption(shortcode)
            result = instagram_event(description)
            if not result:
                logger.info(f"OpenAI returned an empty response for {text}")
                await update.message.reply_text("OpenAI returned an empty response.")
                return ConversationHandler.END
            event = {"name": result["name"],
                    "date": result["date"],
                    "artists":result["artists"],
                    "organizer":username,
                    "location":result["location"],
                    "price":result["price"],
                    "link":text,
                    "raw_descr":description}
            context.user_data['event'] = event
        elif 'dice.fm' in text:
            event = dice.scrape_link(text)
            if not event:
                logger.info(f"Couldn't scrape Dice: {text}")
                await update.message.reply_text("Couldn't scrape this link, sorry!")
                return ConversationHandler.END
            context.user_data['event'] = event
        else:
            response = "Sorry, I can't understand you. Use the command /help to see what I can do."
            await update.message.reply_text(response)
            return ConversationHandler.END
    else:
        context.user_data.pop('type_of_content')
        response = f'Couldn\'t parse your message.\nThis is your last recorded message: {update.message.text}.\n Use the command /help to see what I can do.'
        await update.message.reply_text(response)
        return ConversationHandler.END
    
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
    await update.message.reply_text("Is this correct?", reply_markup=keyboard)
    return CREATED_EVENT

async def save_or_correct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """If the user pressed the Yes button, the JSON is deemed correct and we save it to database 
    and close the conversation.
    If the user pressed the No button then prompts the user for a correct version of the JSON"""
    query = update.callback_query
    await query.answer()
    if query.data == "yes":
        logger.info("User confirmed the event.")
        response = context.user_data.get('event')
        event = (response["name"],response["date"],response["artists"],response["organizer"],response["location"],response["price"],response["link"],response["raw_descr"])
        if not utils.check_date_format(str(response["date"])):
            logger.info(f"User was passing wrong date {str(response['date'])}")
            context.user_data["wrong_date"] = True
            await query.edit_message_text(f"Date {str(response['date'])} is badly formatted, I need YYYY-MM-DD HH:mm:ss")
            reply_keyboard = [["DATE"]]
            await query.message.reply_text(
            "Select the date parameter so we can correct it",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,
                input_field_placeholder="Select the date parameter",
            ),
        )
            return SELECTED_PARAMETER_TO_CORRECT
        with sqlite3.connect('pulse.db') as connection:
            user = update.callback_query.from_user
            logger.info(f'User {user["username"]} inserting event {event[0]} by {event[3]} on date {event[1]}')
            inserted = db_handling.insert_event_if_no_similar(connection, event)
            if not inserted:
                logger.info(f"Event {event[0]} by {event[3]} on date {event[1]} is too similar to one in db")
                context.user_data.pop('event')
                await query.edit_message_text("This event is too similar to one in db. Thanks for your help anyway!")
            else:
                await query.edit_message_text("Ok adding to database! Thanks for your help!")
                if 'instagram' in event[6]:
                    shortcode = utils.get_insta_shortcode(event[6])
                    db_handling.add_igpost_shortcode(conn=connection,shortcode=shortcode)
                html_page.update_webpage(connection,"www/gen_index.html",datetime.today())
                html_page.update_webpage(connection,"www/next_month.html",datetime.today()+relativedelta(months=1))
                context.user_data.pop('event')
        


        return ConversationHandler.END
    else:
        reply_keyboard = [
        ["NAME"], ["DATE"], ["ARTISTS"], ["ORGANIZER"],["LOCATION"],["PRICE"],["LINK"],["RAW_DESCR"]]

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
    if context.user_data.get("wrong_date"):
        context.user_data['to_correct'] = update.message.text.lower()
        logger.info("Asking to correct wrong date")
        await update.message.reply_text(f"Send a correctly formatted date (YYYY-MM-DD HH:mm:ss), previous one was {context.user_data['event']['date']}")
        context.user_data.pop("wrong_date")
        return ASKED_FOR_CORRECTION
    else:
        context.user_data['to_correct'] = update.message.text.lower()
        logger.info(f"Asked to correct: {context.user_data['to_correct']}")
        await update.message.reply_text("Send me your correction:",reply_markup=ReplyKeyboardRemove())
        return ASKED_FOR_CORRECTION

async def correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves kind of content that the user has selected and prompts for the content"""
    parameter_to_correct = context.user_data['to_correct']
    context.user_data.pop('to_correct')
    logger.info(f"Correcting: {parameter_to_correct}")
    context.user_data['event'][parameter_to_correct] = update.message.text
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

def create_new_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("new", new)],
        states={
            SELECTED_CONTENT: [
                MessageHandler(filters.Regex("^(IG LINK|DICE LINK|IG SCREEN|FB SCREEN)$"), sendme)],
            ASKED_FOR_CONTENT: [MessageHandler(filters.TEXT | filters.PHOTO & (~ filters.COMMAND), answer)],
            CREATED_EVENT: [CallbackQueryHandler(save_or_correct)],
            SELECTED_PARAMETER_TO_CORRECT: [MessageHandler(filters.Regex(
                        "^(NAME|DATE|ARTISTS|ORGANIZER|LOCATION|PRICE|LINK|RAW_DESCR)$"), ask_correction)],
            ASKED_FOR_CORRECTION: [MessageHandler(filters.TEXT & (~ filters.COMMAND), correct)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],conversation_timeout=600
    )
