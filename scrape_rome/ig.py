from datetime import datetime, timedelta
from itertools import dropwhile, takewhile
import time
import os
import instaloader
import sqlite3
from ftfy import fix_text
from . import db_handling
from .openai import get_event_info
import json

USERNAMES_TO_SCRAPE = ['angelo_mai_roma', 'forte_antenne', 'nuur.xyz']

def return_username_caption(link):
    """ Return caption and username from link"""
    L = instaloader.Instaloader()
    post = instaloader.Post.from_shortcode(L.context, link.split('/')[-2])
    return post.caption, post.owner_username

# Save all
def scrape_and_insert(users: list):
    L = instaloader.Instaloader()

    SINCE = datetime.today()
    UNTIL = SINCE - timedelta(days=10)

    # DB is locked from concurrency
    with sqlite3.connect('pulse.db') as connection:
        for user in users:
            profile = instaloader.Profile.from_username(L.context, user)
            posts = profile.get_posts()
            for post in takewhile(lambda p: p.date > UNTIL, dropwhile(lambda p: p.date > SINCE, posts)):
                caption = post.caption
                shortcode = post.shortcode
                # no post caption, no scraping
                if caption:
                    # if the shortcode is not in the db it means this is a new post and it needs to be scraped
                    if not db_handling.is_igpost_shortcode_in_db(connection, shortcode):
                        response = json.loads(get_event_info(fix_text(caption), source='instagram', key=os.environ['OPENAI_KEY'], username=post.owner_username, link=f'instagram.com/{shortcode}'))
                        event = (response["name"],response["date"],response["artists"],response["organizer"],response["location"],response["price"],response["link"])
                        duplicated = db_handling.insert_event_if_no_similar(connection, event)
                        if duplicated:
                            print(f"This event is too similar to {duplicated[0]} by {duplicated[1]} happening on same date, won't be added.")
                        else:
                            print(f'Inserted {event}')
                    else:
                        print(f'Already scraped ig post with shortcode {shortcode}, no action')
                time.sleep(2)
            time.sleep(30)