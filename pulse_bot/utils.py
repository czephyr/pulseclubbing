from functools import wraps
from scrape_rome.db_handling import return_valid_events_by_date
import sqlite3
import datetime


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

def create_tg_post(start_date, end_date):
    with sqlite3.connect('pulse.db') as connection:
        events = return_valid_events_by_date(connection, start_date, end_date)
    message = "Questo weekend Stase.it consiglia:\n"
    event_by_date = {}
    for event in events:
        name = event[0]
        date = event[1].split(' ')[0]
        organizer = event[2]
        link = event[6]
        event_msg = f"» @{organizer} || {name}\n{link}\n\n"
        if date in event_by_date:
            event_by_date[date] += event_msg
        else:
            event_by_date[date] = event_msg
    for date, msg in event_by_date.items():
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        day = date_obj.strftime('%A %d %B')
        message += f"{day}\n{msg}\n"
    return message
