from datetime import datetime, timedelta
from itertools import dropwhile, takewhile
import time
import os
import logging
import instaloader
import sqlite3
from ftfy import fix_text
from . import db_handling
from .openai import instagram_event
import re
import random

logger = logging.getLogger("mannaggia")

USERNAMES_TO_SCRAPE = {
    "Angelo Mai": "angelo_mai_roma",
    "Nuur": "nuur.xyz",
    "Trenta Formiche": "trenta_formiche",
    "Magma": "arci_magma",
    "Club Arciliuto": "clubarciliuto",
    "Kurage": "kurage_roma",
    "Campo Magnetico": "campomagneticoroma",
    "Blaze": "blaze.roma",
    "Vetro Enoteca": "vetro_enoteca",
    "Club Industria": "club_industria",
    "Reveries": "reveries_rome",
    # "Baronato": "baronato4bellezze", # Never announce beforehand, but events always take place on Tuesday, we could also just add them with a cronjob
    # "Teatro delle Bellezze": "teatrodellebellezze", # TODO Creates posts with multiple events in the description, we really need to add it but we need an handler for multiple events
    # "Forte Antenne": "forte_antenne", # Removed 'cause they post too much
}


def return_username_caption(shortcode):
    """Return caption and username from link"""
    L = instaloader.Instaloader()
    try:
        L.load_session_from_file(
            os.getenv("INSTAGRAM_USERNAME"), filename=os.getenv("INSTAGRAM_SESSION_FILE")
        )
    except Exception as e:
        logger.error(f"Error loading session file: {e}")
        pass
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    caption = post.caption
    username = post.owner_username
    date = (post.date).strftime("%Y-%m-%d %H:%M:%S")
    return caption, username, date


def scrape(delta_days):
    logger.info(f"Scraping IG with delta {delta_days}...")
    wait_time = random.randint(1000,20000)
    time.sleep(wait_time)
    logger.info(f"Will wait {wait_time}")
    L = instaloader.Instaloader()
    try:
        L.load_session_from_file(
            os.getenv("INSTAGRAM_USERNAME"), filename=os.getenv("INSTAGRAM_SESSION_FILE")
        )
    except Exception as e:
        logger.error(f"Error loading session file: {e}")
        pass
    
    # Scrape posts not older than delta_days days
    SINCE = datetime.today()
    UNTIL = SINCE - timedelta(days=delta_days)

    for organizer, user in USERNAMES_TO_SCRAPE.items():
        logger.info(f"scraping insta user {user} ({organizer})")

        profile = instaloader.Profile.from_username(L.context, user)
        posts = profile.get_posts()
        for post in takewhile(
            lambda p: (p.date > UNTIL or p.is_pinned),
            dropwhile(lambda p: p.date >= SINCE, posts),
        ):
            logger.info(f"Handling post: instagram.com/p/{post.shortcode}")
            caption = post.caption
            shortcode = post.shortcode
            date = (post.date).strftime("%Y-%m-%d %H:%M:%S")
            link = f"https://instagram.com/p/{shortcode}"
            # No post caption, no scraping
            if caption:
                caption = fix_text(caption.lower())
                # If the shortcode is not in the db it means this is a new post and it needs to be scraped
                with sqlite3.connect("pulse.db") as connection:
                    if not db_handling.is_igpost_shortcode_in_db(connection, shortcode):
                        db_handling.add_igpost_shortcode(connection,shortcode)
                        response = instagram_event(caption, date)
                        if not response:
                            logger.info("OpenAI returned an empty response")
                            continue
                        event = (
                            response["name"],
                            response["date"],
                            response["artists"],
                            organizer,
                            response["location"],
                            response["price"],
                            link,
                            caption,
                        )
                        db_handling.insert_event_if_no_similar(connection, event)
                    else:
                        logger.info("already scraped post, no action")
            else:
                logger.info("no caption found for post")

            time.sleep(300 + random.randint(0,300))
        time.sleep(300 + random.randint(0,300))
