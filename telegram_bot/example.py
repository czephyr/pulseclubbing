#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import os
import json
from telegram import __version__ as TG_VER
from PIL import Image
import pytesseract
import cv2
import openai
import instaloader

# Remove the line below if you are not using Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, Updater, CallbackContext
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPEN_AI_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPEN_AI_KEY

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
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
    
    file = await context.bot.get_file(update.message.photo[-1].file_id)
    await file.download_to_drive('./image.jpg')
    extracted_text = pytesseract.image_to_string(Image.open('./image.jpg'))
    
    caption = update.message.caption.lower() if update.message.caption else ''

    if caption == 'instagram' or caption == '':        
        description = extracted_text.split(" ",1)
        result = json.loads(get_event_info(description))
        await update.message.reply_text(result if extracted_text else "Sorry, couldn't extract any text from the image.")
        return
    else:
        await update.message.reply_text("Sorry, I can't understand you. Please send me a photo with the caption 'instagram'")
        return

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if 'instagram.com' in text:
        description, username = ig_post_handler(text)
        result = json.loads(get_event_info(description, username))
        await update.message.reply_text(result if description else "Sorry, couldn't extract any caption from the post.")
        return
    elif 'facebook' in update.message.text:
        await update.message.reply_text("Sorry, I can't handle facebook links yet.")
        return
    else:
        await update.message.reply_text("Sorry, I can't understand you. Use the command /help to see what I can do.")
        return

def get_event_info(description, username='', source='instagram'):
    prompt = f"""
    È il 2023, il seguente messaggio delimitato dalle virgolette è l'estrazione OCR di uno screenshot da cellulare di un post instagram descrivente un evento:
    '{description}'

    Rispondi dando le seguenti variabili in formato json, traendo informazioni solo dalla descrizione del post:

    - datetime: la data estratta dalla descriozione in questo formato 2023-mese-giorno ora_di_partenza:minuto_di_partenza:00
    - nome_evento: il nome dell'evento estratto dalla descrizione
    - artisti: nome degli artisti che suonano separato da una virgola
    - luogo: luogo dell'evento
    - costo: costo del biglietto, se possibile
    - username: lo username dell'account instagram che ha postato l'evento, di solito dopo gli username di chi ha messo like al post e sempre prima della descrizione dell'evento
    - link: https://instagram.com/{username if username else 'inserisci lo username del profilo instagram che ha postato evento'}
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

def ig_post_handler(link):
    L = instaloader.Instaloader()
    post = instaloader.Post.from_shortcode(L.context, link.split('/')[-2])
    return post.caption, post.owner_username

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TG_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # When the user sends a message, check if it contains a photo
    application.add_handler(MessageHandler(filters.PHOTO, photo))

    # When the user sends a message, check if it contains a link
    application.add_handler(MessageHandler(filters.TEXT, link))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == "__main__":
    main()