from telegram import (
    Update,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Cancelled.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END