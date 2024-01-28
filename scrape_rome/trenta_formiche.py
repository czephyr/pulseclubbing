import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from . import db_handling
import sqlite3

logger = logging.getLogger("mannaggia")

def get_events():
    """Return a list of URLs of the events currently in the 30 Formiche website"""

    url = "https://www.30formiche.it"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    events = soup.find("section", {"id": "events"})
    hrefs = events.find_all("a", href=True)
    links = [link.get("href") for link in hrefs]
    links = set(links)
    links = [url + link for link in links]
    return links

def get_time(description="", title=""):
    """
    Utility function to get the time from the description

    Parameters:
        description : str
            The description of the event

    Returns:
        str: the time in the format HH:MM:SS
    """
    keys = ["inizio live", "apertura porte", "inizio concerto"]
    for key in keys:
        pattern = re.compile(rf"{key} *h?\.? *(\d{{1,2}}[:.\d{{0,2}}]*)", re.IGNORECASE)
        match = pattern.search(description)
        if match:
            time = match.group(1).replace('.', ':')
            if len(time.split(":")) == 2:
                time = time + ":00"
            return time
    logger.warning(f"No time found in description for event {title}, using arbitrary time 22:00:00")
    return "22:00:00"

def scrape():
    """Scrape the latest program for 30 Formiche and insert the events in the database"""
    logger.info("Scraping 30 Formiche...")
    links = get_events()
    if not links:
        logger.error("No events found for 30 Formiche")
        return
    events_list = []
    for link in links:
        try:
            r = requests.get(link)
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.find("h1", {"class": "scroll-reveal"}).text.strip()
            date = soup.find("div", {"class": "col-md-4"}).find("p").text.strip()
            description = soup.find("div", {"class": "event-description"}).text.strip()
            time = get_time(description, title)
            # Convert the date and time strings to a datetime object, then format it to a string
            date_and_time = datetime.strptime(date + ' ' + time, '%d %b %Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            event_dict = {
                "title": title,
                "date_and_time": date_and_time,
                "url": link,
                "description": description
            }
            events_list.append(event_dict)
        except Exception as e:
            logger.error(f"Error for event {title} --- {e}")
            pass
    with sqlite3.connect("pulse.db") as connection:
        for event in events_list:
            logger.info(f"Inserting event {event['title']} from 30 Formiche with date {event['date_and_time']}")
            db_handling.insert_event_if_no_similar(
                conn=connection,
                event=(
                    event["title"],
                    event["date_and_time"],
                    "", # No way to retrieve artists here at the moment
                    "Trenta Formiche",
                    "Via Del Mandrione 3",
                    "Piccolo contributo + Tessera Arci",
                    event["url"],
                    event["description"],
                )
            )