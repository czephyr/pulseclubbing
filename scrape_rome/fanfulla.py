import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from . import utils
from . import db_handling
import sqlite3
from .custom_logger import logger 

platforms = ['bandcamp', 'soundcloud', 'spotify', 'youtube', 'mixcloud']

def scrape():
    logger.info("Scraping Fanfulla...")
    html = requests.get('http://www.fanfulla5a.it/2023/10/01/programma-ottobre-2024-2/').content
    # TODO: We are now scraping the whole month, but at the moment we need to insert the link manually
    soup = BeautifulSoup(html, 'lxml')

    events = soup.find_all('div', class_='siteorigin-widget-tinymce')
    events_list = []
    for event in events:
        event_dict = {}
        try:
            day = event.find('h3').text.strip()
            day = ''.join(filter(str.isdigit, day))
            day = datetime.strptime(f'{day} {datetime.now().month} {datetime.now().year}', '%d %m %Y')
        except Exception as e:
            print(e)
            pass
        event_dict['title'] = event.find('h4').text
        event_dict['location'] = 'Fanfulla 5/A Circolo Arci'
        try:
            time = event.find('span', class_='_4n-j fsl').text
            try: # different time conventions
                time = time.split(' ore ')[1]
                if len(time) == 2:
                    time = datetime.strptime(time, '%H')
                elif '.' in time and len(time) == 5:
                    time = time.replace('.', ':')
                    time = datetime.strptime(time, '%H:%M')
            except IndexError:
                time = time.split('dalle ')[1]
                if len(time) == 2:
                    time = datetime.strptime(time, '%H')
                elif '.' in time and len(time) == 5:
                    time = time.replace('.', ':')
                    time = datetime.strptime(time, '%H:%M')
            time = time.strftime('%H:%M')
            event_dict['date_and_time'] = day.replace(hour=int(time.split(':')[0]), minute=int(time.split(':')[1]))
            event_dict["date_and_time"] = event_dict["date_and_time"].strftime('%Y-%m-%d %H:%M:%S')
            urls = [a['href'] for a in event.find_all('a', href=True) if 'facebook' in a['href'] and 'event' in a['href']]
            event_dict['url'] = urls[0] if urls else 'http://www.fanfulla5a.it/'
            # links = [a['href'] for a in event.find_all('a', href=True) if any(platform in a['href'] for platform in platforms)]
            # event_dict['artists_links'] = '; '.join(links) # These two lines are commented because at the moment we don't need to store artists links
            event_dict['description'] = event.text.strip()
            events_list.append(event_dict)
        except AttributeError as e:
            logger.error(f"Error for event {event_dict['title']} --- {e}")
            pass

    with sqlite3.connect('pulse.db') as connection:
        for event in events_list:
            logger.info(f"Inserting event {event['title']} from {'Fanfulla 5/A'} with date {event['date_and_time']}")
            db_handling.insert_event_if_no_similar(conn=connection,event=(event['title'], event['date_and_time'],'','Fanfulla 5/A','Via Fanfulla da Lodi, 5/a','Piccolo contributo + Tessera Arci', event['url'],event_dict['description']))