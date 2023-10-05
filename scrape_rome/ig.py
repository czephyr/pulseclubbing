from datetime import datetime, timedelta
from itertools import dropwhile, takewhile
import time
import os
import logging
import instaloader
import sqlite3
from ftfy import fix_text
from . import db_handling
from .openai import get_event_info
import json
from . import utils

logger = logging.getLogger("mannaggia")

USERNAMES_TO_SCRAPE = [
    "angelo_mai_roma",
    # 'forte_antenne', # Removed 'cause they post too much
    "nuur.xyz",
    "trenta_formiche",
    "arci_magma",
]


def return_username_caption(link):
    """Return caption and username from link"""
    L = instaloader.Instaloader()
    post = instaloader.Post.from_shortcode(L.context, link.split("/")[-2])
    return post.caption, post.owner_username


# Save all
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
        for user in USERNAMES_TO_SCRAPE:
            logger.info(f"scraping insta user {user}")

            profile = instaloader.Profile.from_username(L.context, user)
            posts = profile.get_posts()
            for post in takewhile(
                lambda p: (p.date > UNTIL or p.is_pinned),
                dropwhile(lambda p: p.date >= SINCE, posts),
            ):
                logger.info(f"handling post instagram.com/p/{post.shortcode}")
                caption = post.caption
                shortcode = post.shortcode
                # No post caption, no scraping
                if caption:
                    # If the shortcode is not in the db it means this is a new post and it needs to be scraped
                    if not db_handling.is_igpost_shortcode_in_db(connection, shortcode):
                        response = get_event_info(
                            fix_text(caption.lower()),
                            source="instagram",
                            key=os.environ["OPENAI_API_KEY"],
                            username=post.owner_username,
                            link=f"https://instagram.com/p/{shortcode}",
                        )
                        logger.info(f"OpenAI: {response}")
                        try:
                            response = response[
                                response.find("{") : response.rfind("}") + 1
                            ]
                            response = json.loads(response)
                        except json.decoder.JSONDecodeError:
                            logger.error("Error decoding json")
                            continue
                        if not response:
                            logger.info("Empty response from OpenAI")
                            continue
                        else:
                            if (
                                len(response) > 1
                            ):  # Checking if the json has more than one event
                                # using the try just 'cause I don't have time to test rn
                                try:
                                    logger.info(
                                        "More than one event in json response, skipping"
                                    )
                                    utils.skipped_handling(response)
                                    logger.info("Saved these events in skipped.txt")
                                    continue
                                except Exception as e:
                                    logger.error(f"Error saving skipped events: {e}")
                                    continue
                                # With a more powerful model we could use this below, but gpt3.5-turbo is s**t
                                # for event in response:
                                #     event = (response["name"],response["date"],response["artists"],response["organizer"],response["location"],response["price"],response["link"],caption)
                                #     db_handling.insert_event_if_no_similar(connection, event)
                            else:
                                event = (
                                    response["name"],
                                    response["date"],
                                    response["artists"],
                                    response["organizer"],
                                    response["location"],
                                    response["price"],
                                    response["link"],
                                    caption,
                                )
                            db_handling.insert_event_if_no_similar(connection, event)
                    else:
                        logger.info("already scraped post, no action")
                else:
                    logger.info("no caption found for post")

                time.sleep(2)
            time.sleep(30)
