import logging
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from ftfy import fix_text
from unidecode import unidecode
from . import db_handling
import sqlite3

logger = logging.getLogger("mannaggia")

event_page_url = 'https://www.reveriesmusic.it/events'

months_it_to_en = {
    "gen": "Jan",
    "feb": "Feb",
    "mar": "Mar",
    "apr": "Apr",
    "mag": "May",
    "giu": "Jun",
    "lug": "Jul",
    "ago": "Aug",
    "set": "Sep",
    "ott": "Oct",
    "nov": "Nov",
    "dic": "Dec"
}

def scrape():
    """Scrape reveries' events"""
    events = []
    logger.info('Scraping Reveries...')
    response = requests.get(event_page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for event in soup.find_all(attrs={"data-hook": "events-card"}):
        link = event.find(attrs={"data-hook": "title"}).find('a')['href']
        try:
            date = event.find(attrs={"data-hook": "date"}).text
            date = date.split('–')[0].strip()
            for it, en in months_it_to_en.items():
                date = date.replace(it, en)
            date = datetime.strptime(date, "%d %b %Y, %H:%M")
            if date < datetime.now(): # skip past events
                logger.info(f"Skipping past event {link}")
                continue
            date = date.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Found future event {link} at {date}")
        except Exception as e:
            logger.error(f"Error parsing date for event {link}: {e}")
            continue
        try:
            location = event.find(attrs={"data-hook": "location"}).text
            if 'roma' not in location.lower() and 'rome' not in location.lower(): # skip events not in Rome
                logger.info(f"Skipping event {link} not in Rome")
                continue
            description = unidecode(fix_text(event.find(attrs={"data-hook": "description"}).text))
            title = unidecode(fix_text(event.find(attrs={"data-hook": "title"}).text))
            try:
                event_html = requests.get(link)
                event_soup = BeautifulSoup(event_html.text, 'html.parser')
                try:
                    lineup = event_soup.find(attrs={"data-hook": "about-section-text"}).text
                    lineup = lineup.split('\n')[2:]
                    lineup = ', '.join([unidecode(fix_text(line)) for line in lineup])
                except AttributeError as e:
                    logger.error(f"Error scraping lineup for event {link}: {e}")
                    lineup = ''
                price = event_soup.find(attrs={"data-hook": "price"}).text
            except Exception as e:
                logger.error(f"Error scraping event {link}: {e}")
                lineup = ''
                price = ''
        except Exception as e:
            logger.error(f"Error scraping event {link}: {e}")
            continue
        event = (title, date, lineup, 'Reveries', location, price, link, description)
        events.append(event)
    with sqlite3.connect("pulse.db") as connection:
        for event in events:
            logger.info(f"Inserting event {event[0]} from Reveries with date {event[1]}")
            db_handling.insert_event_if_no_similar(connection, event)
    logger.info('Reveries scraping finished')