from datetime import datetime, timedelta
from itertools import dropwhile, takewhile
import time
import os
import instaloader
import sqlite3
from ftfy import fix_text
from .db_handling import check_ig_shortcode, insert_event
from .openai import get_event_info
import json

USERNAMES_TO_SCRAPE = ['angelo_mai_roma', 'forte_antenne', 'nuur.xyz']

def post_handler(link):
    L = instaloader.Instaloader()
    post = instaloader.Post.from_shortcode(L.context, link.split('/')[-2])
    return post.caption, post.owner_username

# Save all
def update_db(users: list):
    L = instaloader.Instaloader()
    # DB is locked from concurrency
    with sqlite3.connect('pulse.db') as connection:
        for user in users:
            profile = instaloader.Profile.from_username(L.context, user)
            posts = profile.get_posts()
            SINCE = datetime.today()
            UNTIL = SINCE - timedelta(days=10)
            for post in takewhile(lambda p: p.date > UNTIL, dropwhile(lambda p: p.date > SINCE, posts)):
                caption = post.caption
                shortcode = post.shortcode
                if caption is None:
                    pass
                else:
                    if check_ig_shortcode(connection, shortcode):
                        response = json.loads(get_event_info(fix_text(caption), source='instagram', key=os.environ['OPENAI_KEY'], username=post.owner_username, link=f'instagram.com/{shortcode}'))
                        event = (response["name"],response["date"],response["artists"],response["organizer"],response["location"],response["price"],response["link"])
                        insert_event(connection, event)
                        print(f'Inserted {event}')
                    else:
                        print(f'Already inserted {shortcode}')
                        pass
                time.sleep(2)
            time.sleep(30)