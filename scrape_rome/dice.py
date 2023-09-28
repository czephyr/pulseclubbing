import requests
import time
import json
from .custom_logger import logger
from . import db_handling
from ftfy import fix_text
import sqlite3
from bs4 import BeautifulSoup

VENUES_TO_SCRAPE = {
    # 'Monk': 'monk---sala-teatro-o58r', # Monk occasionally has orrible events, we'll check it manually
    'Forte Antenne': 'forte-antenne-96yd',
}

REQUEST_HEADER = {
    "User-Agent": "Chrome/91.0.4472.124", 
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def scrape():
    logger.info(f'Scraping {len(VENUES_TO_SCRAPE)} venues from Dice')
    with sqlite3.connect('pulse.db') as connection:
        for venue, venue_id in VENUES_TO_SCRAPE.items():
            logger.info(f'Scraping {venue} on Dice')
            url = f'https://dice.fm/venue/{venue_id}'
            try:
                r = requests.get(url, headers=REQUEST_HEADER)
                soup = BeautifulSoup(r.content, 'html.parser')
                data = soup.find('script', type='application/ld+json').string
                data = json.loads(data)
                for event in data['event']:
                    name = fix_text(event['name'])
                    startdate = event['startDate']
                    startdate = startdate.replace('T', ' ').split('+')[0]
                    url = event['url']
                    address = event['location']['address']
                    description = fix_text(event['description'])
                    event = (name, startdate, '', venue, address, '', url, description) # Artists and price are empty atm
                    db_handling.insert_event_if_no_similar(connection, event)
            except json.decoder.JSONDecodeError as e:
                logger.error(f'JSONDecodeError: {e}')
                continue
            except Exception as e:
                logger.error(f'Exception: {e}')
                continue
            time.sleep(10)
    logger.info('Dice scraping finished')


def scrape_link(url):
    logger.info(f'Scraping single {url} on Dice')
    try:
        r = requests.get(url, headers=REQUEST_HEADER)
        soup = BeautifulSoup(r.content, 'html.parser')
        data = soup.find('script', type='application/ld+json').string
        data = json.loads(data)
        name = fix_text(data['name'])
        startdate = data['startDate']
        startdate = startdate.replace('T', ' ').split('+')[0]
        organizer = data['location']['name']
        address = data['location']['address']
        description = fix_text(data['description'])
        price = soup.find('div', class_='EventDetailsCallToAction__Price-sc-12zjeg-6')
        price = ' '.join([p.text for p in price.find_all('span')])
        try:
            # We are currently getting the entire lineup as a single string,
            # when too long only few artists are shown and the rest is replaced by 'and x others'.
            artists = soup.find('div', class_='EventDetailsLineup__ArtistTitle-gmffoe-10').text.strip()
        except AttributeError:
            # When there is no artist listed, the div is not present
            artists = ''
        response = {
            "name": name,
            "date": startdate,
            "artists": artists,
            "organizer": organizer,
            "location": address,
            "price": price,
            "link": url,
            "raw_descr": description
        }
        return response
    except json.decoder.JSONDecodeError as e:
        logger.error(f'JSONDecodeError: {e}')
    except Exception as e:
        logger.error(f'Exception: {e}')