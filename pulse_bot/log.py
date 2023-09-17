import os
from telegram import (
    Update,
    ReplyKeyboardRemove
)
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    ContextTypes,
)

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("app.log","r") as f:
        last_run = f.read().split("-"*300)[-1]
    with open("last_run.log","w") as f:
        f.write(last_run)
    with open("last_run.log","rb") as f:
        context.bot.send_document(chat_id=update.effective_chat.id, document=f)
    os.remove("last_run.log")
    return ConversationHandler.END