from functools import wraps

allowed_ids = [474799562, 290855718]

def restricted(func):
    """Restrict usage of a function to allowed users only and replies if necessary"""
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        # Check if the update is a message or callback query and get user_id accordingly
        if hasattr(update, 'effective_user') and update.effective_user:
            user_id = update.effective_user.id
        elif hasattr(update, 'callback_query') and update.callback_query:
            user_id = update.callback_query.from_user.id
        else:
            print("WARNING: Could not determine user ID.")
            return  # Exit if user ID cannot be determined

        # Check if user is allowed
        if user_id not in allowed_ids:
            print(f"WARNING: Unauthorized access denied for {user_id}.")
            # Send a message if it's a regular update or edit message for callback query
            if hasattr(update, 'message'):
                await context.bot.send_message(chat_id=user_id, text='User disallowed.')
            elif hasattr(update, 'callback_query'):
                await update.callback_query.answer(text='User disallowed.', show_alert=True)
            return  # Exit function

        return await func(update, context, *args, **kwargs)
    return wrapped
