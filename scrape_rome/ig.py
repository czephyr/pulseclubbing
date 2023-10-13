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
import json
from . import utils

logger = logging.getLogger("mannaggia")

USERNAMES_TO_SCRAPE = {
    "Angelo Mai": "angelo_mai_roma",
    # "Forte Antenne": "forte_antenne", # Removed 'cause they post too much
    "Nuur": "nuur.xyz",
    "Trenta Formiche": "trenta_formiche",
    "Magma": "arci_magma",
}


def return_username_caption(link):
    """Return caption and username from link"""
    L = instaloader.Instaloader()
    L.load_session_from_file(
        os.getenv("INSTAGRAM_USERNAME"), filename=os.getenv("INSTAGRAM_SESSION_FILE")
    )
    post = instaloader.Post.from_shortcode(L.context, link.split("/")[-2])
    return post.caption, post.owner_username


def scrape(delta_days):
    logger.info(f"Scraping IG with delta {delta_days}...")
    L = instaloader.Instaloader()

    L.load_session_from_file(
        os.getenv("INSTAGRAM_USERNAME"), filename=os.getenv("INSTAGRAM_SESSION_FILE")
    )

    # will scrape posts not older than delta_days days
    SINCE = datetime.today()
    UNTIL = SINCE - timedelta(days=delta_days)

    # DB is locked from concurrency
    with sqlite3.connect("pulse.db") as connection:
        for organizer, user in USERNAMES_TO_SCRAPE.items():
            logger.info(f"scraping insta user {user} ({organizer})")

            profile = instaloader.Profile.from_username(L.context, user)
            posts = profile.get_posts()
            for post in takewhile(
                lambda p: (p.date > UNTIL or p.is_pinned),
                dropwhile(lambda p: p.date >= SINCE, posts),
            ):
                logger.info(f"handling post instagram.com/p/{post.shortcode}")
                caption = post.caption
                shortcode = post.shortcode
                link = f"https://instagram.com/p/{shortcode}"
                # No post caption, no scraping
                if caption:
                    caption = fix_text(caption.lower())
                    # If the shortcode is not in the db it means this is a new post and it needs to be scraped
                    if not db_handling.is_igpost_shortcode_in_db(connection, shortcode):
                        response = instagram_event(caption)
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
                        db_handling.add_igpost_shortcode(connection,shortcode)
                    else:
                        logger.info("already scraped post, no action")
                else:
                    logger.info("no caption found for post")

                time.sleep(2)
            time.sleep(30)
