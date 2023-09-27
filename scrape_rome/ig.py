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
from .custom_logger import logger


USERNAMES_TO_SCRAPE = ['angelo_mai_roma',
                       'forte_antenne',
                       'nuur.xyz',
                       'trenta_formiche',
                       'arci_magma']

def return_username_caption(link):
    """ Return caption and username from link"""
    L = instaloader.Instaloader()
    post = instaloader.Post.from_shortcode(L.context, link.split('/')[-2])
    return post.caption, post.owner_username

# Save all
def scrape(delta_days):
    logger.info(f"Scraping IG with delta {delta_days}...")
    L = instaloader.Instaloader()

    L.load_session_from_file(os.getenv("INSTAGRAM_USERNAME"),filename=os.getenv("INSTAGRAM_SESSION_FILE"))

    # will scrape posts not older than delta_days days
    SINCE = datetime.today()
    UNTIL = SINCE - timedelta(days=delta_days)

    # DB is locked from concurrency
    with sqlite3.connect('pulse.db') as connection:
        for user in USERNAMES_TO_SCRAPE:
            logger.info(f"scraping insta user {user}")

            profile = instaloader.Profile.from_username(L.context, user)
            posts = profile.get_posts()
            for post in takewhile(lambda p: (p.date > UNTIL or p.is_pinned), dropwhile(lambda p: p.date >= SINCE, posts)):
                logger.info(f"handling post instagram.com/p/{post.shortcode}")
                caption = post.caption
                shortcode = post.shortcode
                # no post caption, no scraping
                if caption:
                    # if the shortcode is not in the db it means this is a new post and it needs to be scraped
                    if not db_handling.is_igpost_shortcode_in_db(connection, shortcode):
                        #TODO: create a logic to recognize when the returned 
                        # json is empty, which means ChatGPT chose that the event is not 
                        # a club night
                        response = get_event_info(fix_text(caption.lower()), source='instagram', key=os.environ['OPENAI_API_KEY'], username=post.owner_username, link=f'https://instagram.com/p/{shortcode}')
                        logger.info(f"OpenAI: {response}")
                        try:
                            response = response[response.find('{'):response.rfind('}')+1]
                            response = json.loads(response)
                        except(json.decoder.JSONDecodeError):
                            logger.error('Error decoding json')
                            continue
                        event = (response["name"],response["date"],response["artists"],response["organizer"],response["location"],response["price"],response["link"],caption)
                        db_handling.insert_event_if_no_similar(connection, event)
                    else:
                        logger.info('already scraped post, no action')
                else:
                    logger.info("no caption found for post")

                time.sleep(2)
            time.sleep(30)