from telegram import (
    Update,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
)
import logging

logger = logging.getLogger("mannaggia")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    logger.info("User cancelled the conversation.")
    return ConversationHandler.END