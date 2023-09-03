#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

import os

from telegram import __version__ as TG_VER
from PIL import Image
import pytesseract
import cv2

import openai

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPEN_AI_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPEN_AI_KEY

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    file = await context.bot.get_file(update.message.photo[-1].file_id)
    await file.download_to_drive('./image.jpg')
    extracted_text = pytesseract.image_to_string(Image.open('./image.jpg'))

    username, description = extracted_text.split(" ",1)
    result = get_event_info(description)
    await update.message.reply_text(result if extracted_text else "Sorry, couldn't extract any text from the image.")
    


def get_event_info(description):
    prompt = f"""
    È il 2023, il seguente messaggio delimitato dalle virgolette è la caption di un post instagram descrivente un evento:
    '{description}'

    Rispondi dando le seguenti variabili:

    - datetime: la data estratta dalla descriozione in questo formato 2023/mese/giornoTora_di_partenza:minuto_di_partenza:00Z
    - nome_evento: il nome dell'evento estratto dalla descrizione
    - artisti: nome degli artisti che suonano separato da una virgola
    - luogo: luogo dell'evento
    - costo: costo del biglietto, se possibile
    """
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].text.strip()

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TG_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.PHOTO, photo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == "__main__":
    main()