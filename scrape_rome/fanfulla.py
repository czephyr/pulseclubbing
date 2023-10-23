import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import calendar
from . import utils
from . import db_handling
import sqlite3

logger = logging.getLogger("mannaggia")
platforms = ['bandcamp', 'soundcloud', 'spotify', 'youtube', 'mixcloud']


def get_program():
    """Return the URL of the latest program for Fanfulla. \n
    If the current day is in the last five days of the month, return the URL of the program for the next month.
    
    Returns:
        str: URL of the program"""
    
    today = datetime.now()
    # Check if it's the last five days of the month and get the month name and number
    if today.day > calendar.monthrange(today.year, today.month)[1] - 5:
        next_month = today.replace(day=1) + timedelta(days=31)
        month = next_month.month
        month_name = next_month.strftime("%B")
    else:
        month = today.month
        month_name = today.strftime("%B")
    
    en_to_it = {
        "January": "Gennaio",
        "February": "Febbraio",
        "March": "Marzo",
        "April": "Aprile",
        "May": "Maggio",
        "June": "Giugno",
        "July": "Luglio",
        "August": "Agosto",
        "September": "Settembre",
        "October": "Ottobre",
        "November": "Novembre",
        "December": "Dicembre"
    }
    month_name_it = en_to_it.get(month_name)
    
    # Get the program page
    response = requests.get('http://www.fanfulla5a.it/category/mese/')
    soup = BeautifulSoup(response.text, 'lxml')

    # Find the link to the program
    program_link = None
    articles = soup.find_all('article')
    for article in articles:
        header = article.find('h2', class_='archive-title')
        if header and month_name_it in header.text:
            program_link = header.find('a')['href']
            break
    return month, program_link


def scrape():
    """Scrape the latest program for Fanfulla 5/A and insert the events in the database"""
    logger.info("Scraping Fanfulla...")
    month, link = get_program()
    if not link:
        logger.error("No program link found for Fanfulla 5/A")
        return
    # Handle the case in which the program is for the next year
    if month == 1 and datetime.now().month == 12:
        year = datetime.now().year + 1
    else:
        year = datetime.now().year
    logger.info(f"Found program link for Fanfulla 5/A: {link}")
    html = requests.get(link).content
    soup = BeautifulSoup(html, 'lxml')
    events = soup.find_all('div', class_='siteorigin-widget-tinymce')
    events_list = []
    for event in events:
        event_dict = {}
        try:
            day = event.find('h3').text.strip()
            day = ''.join(filter(str.isdigit, day))
            day = datetime.strptime(f'{day} {month} {year}', '%d %m %Y')
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