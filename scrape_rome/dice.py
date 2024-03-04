import logging
from seleniumbase import Driver
import time
import json
from . import db_handling
from ftfy import fix_text
import sqlite3
from bs4 import BeautifulSoup

logger = logging.getLogger("mannaggia")

VENUES_TO_SCRAPE = {
    # 'Monk': 'monk---sala-teatro-o58r', # Monk occasionally has orrible events, we'll check it manually
    # 'Forte Antenne': 'forte-antenne-96yd',
    'Hacienda': 'hacienda-6568',
}

def scrape():
    logger.info(f'Scraping {len(VENUES_TO_SCRAPE)} venues from Dice')
    with sqlite3.connect('pulse.db') as connection:
        for venue, venue_id in VENUES_TO_SCRAPE.items():
            logger.info(f'Scraping {venue} on Dice')
            url = f'https://dice.fm/venue/{venue_id}'
            try:
                driver = Driver(uc=True)
                driver.uc_open_with_reconnect(url)
                html_content = driver.get_page_source()
                driver.quit()
                soup = BeautifulSoup(html_content, 'html.parser')
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
                    logging.info(f'Inserting event {name} from {venue} with date {startdate}')
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
        driver = Driver(uc=True)
        driver.uc_open_with_reconnect(url)
        html_content = driver.get_page_source()
        driver.quit()
        soup = BeautifulSoup(html_content, 'html.parser')
        data = soup.find('script', type='application/ld+json').string
        data = json.loads(data)
        name = fix_text(data['name'])
        startdate = data['startDate']
        startdate = startdate.replace('T', ' ').split('+')[0]
        organizer = data['location']['name']
        address = data['location']['address']
        description = fix_text(data['description'])
        price = soup.find('div', class_='EventDetailsCallToAction__Price-sc-77f1a107-6')
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
        logger.debug(f'Dice event response:\n{response}')
        return response
    except json.decoder.JSONDecodeError as e:
        logger.error(f'JSONDecodeError: {e}')
        return None
    except Exception as e:
        logger.error(f'Exception: {e}')
        return None