import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger("mannaggia")

REQUEST_HEADER = {
    "User-Agent": "Chrome/91.0.4472.124", 
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def scrape_link(url):
    logger.info(f'Scraping single {url} on Eventbrite')
    try:
        r = requests.get(url, headers=REQUEST_HEADER)
        soup = BeautifulSoup(r.content, 'html.parser')
        name = soup.find('h1', class_='event-title').text.strip()
        date = soup.find('time', class_='start-date')['datetime']
        time = soup.find('span', class_='date-info__full-datetime').text.strip()
        start_time = time.split('-')[0].strip().split('·')[1].strip()
        start_time = convert_time(start_time)
        startdate = f'{date} {start_time}'
        end_time = time.split('-')[1].strip().split('·')[1].strip().split(' ')[0]
        end_time = convert_time(end_time)
        location_info_div = soup.find('div', class_='location-info__address')
        organizer = location_info_div.find('p', class_='location-info__address-text').text.strip()
        location = location_info_div.text.strip().replace(name, '').replace('Show map', '').strip()
        description = soup.find('p', class_='summary').text.strip()
        url = url.split('?')[0]
        response = {
            'name': name,
            'date': startdate,
            'artists': '',
            'organizer': organizer,
            'location': location,
            'price': '',
            'link': url,
            'raw_descr': description
        }
        logger.debug(f'Eventbrite response: {response}')
        return response
    except Exception as e:
        logger.error(f'Exception: {e}')
        return None


def convert_time(time):
    """
    Convert time from 12h to 24h format

    Args:
        time (str): time in 12h format

    Returns:
        str: time in 24h format

    Examples:
        >>> convert_time('9:30pm')
        '21:30:00'
        >>> convert_time('9pm')
        '21:00:00'
    """
    if ':' in time:
        standard_time = datetime.strptime(time, '%I:%M%p').strftime('%H:%M:%S')
    else:
        standard_time = datetime.strptime(time, '%I%p').strftime('%H:%M:%S')
    return standard_time