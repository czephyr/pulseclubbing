import requests
import random
import time
import sqlite3
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from . import utils
from . import db_handling
import logging 

import cloudscraper
from bs4 import BeautifulSoup
import json

logger = logging.getLogger("mannaggia")

CLUBS = { # IDs must be strings to perform the request correctly
    'Forte Antenne': '190667',
    'Hotel Butterfly': '139767',
    # 'Wood Natural Bar': '216590', # Solo stagione estiva
    # 'Cieloterra': '165998',
    # 'Andrea Doria': '32487',
    # 'Nuur': '215874',
    # 'Circolo Degli Illuminati': '36463',
    # 'Brancaleone': '4916',
    # 'Rashomon': '5861',
    # 'La Redazione': '210246',
    # 'Officine Farneto': '19276',
    'Magick Bar': '153706',
    # 'Città Dell\'Altra Economia': '46480',
    'Piazza Gianicolo': '217099',
    'Villa Ada': '106550',
    'Cave di tufo': '215874'
}


def scrape():

    def get_artists(json_data):
        artists = {}
        for x in json_data["props"]["apolloState"]:
            if 'Artist' in x:
                id = json_data["props"]["apolloState"][x]['id']
                name = json_data["props"]["apolloState"][x]['name']
                artists[id] = name
        return artists

    def get_events(json_data, artists_dict, venue_name):
        venue_events = []
        for x in json_data["props"]["apolloState"]:
            if 'Event' in x and 'Image' not in x:
                try:
                    event = json_data["props"]["apolloState"][x]
                    id = event['id']
                    title = event['title']
                    try:
                        date = event['startTime']
                    except KeyError:
                        date = event['date']
                    url = f'https://ra.co/events/{id}'
                    artists_ids_list = []
                    for artist in event['artists']:
                        artist_id = artist['__ref'].split(':')[-1]
                        artists_ids_list.append(artist_id)
                    artists = ', '.join([artists_dict[artist_id] for artist_id in artists_ids_list])

                    flat_event = {
                        'title': title,
                        'date': date,
                        'artists': artists,
                        'venue_name': venue_name,
                        'url': url
                    }

                    venue_events.append(flat_event)

                except Exception as exception:
                    print(f'Error {exception} in scraping an event in {club_name}: {exception}')
                    continue

        return venue_events
    
    logger.info("Scraping RA...")

    # Initializing the scraper
    scraper = cloudscraper.create_scraper(browser={'browser': 'firefox','platform': 'windows','mobile': False})

    # Creating an empty list to store the flattened events for all clubs
    flattened_events = []

    for club_name, club_value in CLUBS.items():
        try:
            logger.info(f"Scraping club {club_name} with ID {club_value}")
            response = scraper.get(f"https://ra.co/clubs/{club_value}/events").content
            soup = BeautifulSoup(response, 'html.parser')
            events = soup.find('script', type='application/json').string
            json_data = json.loads(events)
            artists = get_artists(json_data)
            events = get_events(json_data, artists, club_name)
            flattened_events.extend(events)
            time.sleep(2+random.uniform(0, 1))
        except Exception as exception:
            logger.error(f'Error {exception} in scraping {club_name}: {exception}')
            # continue # Maybe is better to not continue if an error occurs

    with sqlite3.connect('pulse.db') as connection:
        for event in flattened_events:
            date_object = datetime.strptime(event['date'],'%Y-%m-%dT%H:%M:%S.%f')
            formatted_date = date_object.strftime('%Y-%m-%d %H:%M:%S')
            event = (event['title'], formatted_date, event['artists'], event['venue_name'], event['venue_name'], '-1', event['url'], '')
            db_handling.insert_event_if_no_similar(connection, event)

    logger.info("RA scraping finished")


def scrape_from_json(): # Deprecated method
    logger.info("Scraping RA...")
    # Creating an empty list to store the flattened events for all clubs
    flattened_events = []

    # Looping through the clubs
    for club_name, club_value in CLUBS.items():
        logger.info(f"Scraping club {club_name} with ID {club_value}")
        headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'it-IT,it;q=0.5',
        'Content-Length': '1447',
        'Content-Type': 'application/json',
        'Cookie': 'genre=AE793987E4F665D5E9F5522768DA21F039C41F1241DBB813A053FDBBD13143FEC6215510081376610AFB53CD3333FF3B94838341F4E9648327C5E25586437847AA61273BFD6E6FDE4121D7D1021215AA9805EAE7FF8EBE5D1D012C260CAC031524796D16729F2D165850F6797B5B66993AE2829D0187A25464EAC120D8F6B49C613E821D4090C03DBA856174C1E0FF9E622FA30878DB66BF2BB824B6243DE8DFBCAD690074D790A562A09EC938B439B45F2935DE4F6A87904E2EA18A74E5E637B120D87C66EE463D3C2A08B9DBD70EE2D5BCD6C5FD52872B9EA2B616545B59F6F3598440E69054893EE29D39F8E194C8DAAF6D06; ravelinDeviceId=rjs-ecce1a63-a412-483a-9049-34f1df11ecd8; ra_content_language=en; ravelinSessionId=rjs-ecce1a63-a412-483a-9049-34f1df11ecd8:5f8a5610-2ed1-4b8e-a262-ab2cf949ccd3; lvl1=ec2; lvl2=7c60b3bba29595a9; ASP.NET_SessionId=qoheystiyxfssmimedlbih3v; RALang=it; sid=31cb676b-6bdf-423e-a1ce-2220688cacb5; mp_92ee4b4275be9eef375a8c024ded64c3_mixpanel=%7B%22distinct_id%22%3A%20%22189a7946d5dcdc-01535fee342337-26031c51-121b04-189a7946d5e10c9%22%2C%22%24device_id%22%3A%20%22189a7946d5dcdc-01535fee342337-26031c51-121b04-189a7946d5e10c9%22%2C%22%24search_engine%22%3A%20%22duckduckgo%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.it%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.it%22%2C%22ExperimentData%22%3A%20%5B%0A%20%20%20%20%22Enabling%20Festivals%20in%20global%20navigation%3Adisabled%22%2C%0A%20%20%20%20%22Hide%20interested%20(roll%20call)%20count%3Adisabled%22%2C%0A%20%20%20%20%22Promoter%20ticket%20fee%20type%3Adisabled%22%2C%0A%20%20%20%20%22Personalized%20popular%20event%20listings%20for%20logged%20in%20users%3Adisabled%22%2C%0A%20%20%20%20%22Enabling%20cookie%20consent%20banners%3ATop%22%2C%0A%20%20%20%20%22Enabling%20Fourth%20Link%20in%20global%20navigation%3Aoff%22%0A%5D%7D; ra_mp_experimentdata=%5B%22Enabling%20Festivals%20in%20global%20navigation%3Adisabled%22%2C%22Hide%20interested%20(roll%20call)%20count%3Adisabled%22%2C%22Promoter%20ticket%20fee%20type%3Adisabled%22%2C%22Personalized%20popular%20event%20listings%20for%20logged%20in%20users%3Adisabled%22%2C%22Enabling%20cookie%20consent%20banners%3ATop%22%2C%22Enabling%20Fourth%20Link%20in%20global%20navigation%3Aoff%22%5D; datadome=5vxsxbkmbI8-ByXDXV2Cy57u7N9ekZmyZFxn~2FwVF6sCXWP0o5bPOEJUzPVeoDpAwqR63bVFFdaMGo7-W5VarWIiqU56T~ROYzp88WN_sXUSfuuk5r4ec~MWhMZh_ei; __cf_bm=mIZPwp3wi_Pc6R9yNC2ixw9y10sNiaUdDp3Q_6PuuVI-1691442723-0-AVAK/mpvGw9MpppAvVVclF25+F4LLGueslOmh1cVHPADwoq01aOTvT623nzA6i+YPOT+w+3Sw7dlYEmcV4c9LdM=',
        'Origin': 'https://ra.co',
        'Ra-Content-Language': 'en',
        'Referer': 'https://ra.co/clubs/{club_value}/events',
        'Sec-Ch-Ua': '"Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Model': '""',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.1155.0 Safari/537.36',
        'X-Access-Control-Allow-Origin': 'https://ra.co',
        'X-Apollo-Tracing': '1',
        'X-Bazaarvoice-Api': '1',
        }

        json_data = {
            "operationName": "GET_DEFAULT_EVENTS_LISTING",
            "variables": {
                "indices": ["EVENT"],
                "pageSize": 20, # Maximum number of events per page
                "page": 1,
                "aggregations": [],
                "filters": [{"type": "CLUB", "value": club_value},
                            {"type": "DATERANGE", "value": f"{{\"gte\":\"{date.today().strftime('%Y-%m-%dT00:00:00.000Z')}\"}}"}, 
                            {"type": "DATERANGE", "value": f"{{\"lte\":\"{(date.today() + relativedelta(months=+1, day=+31)).strftime('%Y-%m-%dT00:00:00.000Z')}\"}}"}
                            ],
                "sortOrder": "ASCENDING",
                "sortField": "DATE",
                "baseFilters": [{"type": "CLUB", "value": club_value},
                                {"type": "DATERANGE", "value": f"{{\"gte\":\"{date.today().strftime('%Y-%m-%dT00:00:00.000Z')}\"}}"},
                                {"type": "DATERANGE", "value": f"{{\"lte\":\"{(date.today() + relativedelta(months=+1, day=+31)).strftime('%Y-%m-%dT00:00:00.000Z')}\"}}"}
                                ]
            },
            "query":"query GET_DEFAULT_EVENTS_LISTING($indices: [IndexType!], $aggregations: [ListingAggregationType!], $filters: [FilterInput], $pageSize: Int, $page: Int, $sortField: FilterSortFieldType, $sortOrder: FilterSortOrderType, $baseFilters: [FilterInput]) {\n  listing(indices: $indices, aggregations: [], filters: $filters, pageSize: $pageSize, page: $page, sortField: $sortField, sortOrder: $sortOrder) {\n    data {\n      ...eventFragment\n      __typename\n    }\n    totalResults\n    __typename\n  }\n  aggregations: listing(indices: $indices, aggregations: $aggregations, filters: $baseFilters, pageSize: 0, sortField: $sortField, sortOrder: $sortOrder) {\n    aggregations {\n      type\n      values {\n        value\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment eventFragment on IListingItem {\n  ... on Event {\n    id\n    title\n    attending\n    date\n    startTime\n    contentUrl\n    queueItEnabled\n    flyerFront\n    newEventForm\n    images {\n      id\n      filename\n      alt\n      type\n      crop\n      __typename\n    }\n    artists {\n      id\n      name\n      __typename\n    }\n    venue {\n      id\n      name\n      contentUrl\n      live\n      area {\n        id\n        name\n        urlName\n        country {\n          id\n          name\n          urlCode\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    pick {\n      id\n      blurb\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"
        }

        response = requests.post('https://ra.co/graphql', json=json_data, headers=headers)

        try:
            # Extracting the events
            events = response.json()['data']['listing']['data']
            if not events:
                logger.info(f"No events found for {club_name}")
                continue
            # Looping through the events to flatten the nested structure
            for event in events:
                flat_event = {
                    'id': event['id'],
                    'title': utils.clean_text(event['title'], source='resident_advisor'),
                    'attending': event['attending'],
                    'date': event['date'],
                    'startTime': event['startTime'],
                    'contentUrl': event['contentUrl'],
                    'queueItEnabled': event['queueItEnabled'],
                    'flyerFront': event['flyerFront'],
                    'newEventForm': event['newEventForm'],
                    'venue_id': event['venue']['id'],
                    'venue_name': event['venue']['name'],
                    'venue_contentUrl': event['venue']['contentUrl'],
                    'venue_live': event['venue']['live'],
                    'area_id': event['venue']['area']['id'],
                    'area_name': event['venue']['area']['name'],
                    'country_id': event['venue']['area']['country']['id'],
                    'country_name': event['venue']['area']['country']['name'],
                    'club_name': club_name
                }
                # Concatenating artist names
                artist_names = ', '.join([artist['name'] for artist in event['artists']])
                flat_event['artists'] = artist_names
                # Adding the flattened event to the list
                flattened_events.append(flat_event)
                time.sleep(2+random.uniform(0, 1))
        except Exception as exception:
            logger.error(f'Error {exception} in scraping {club_name}: {exception}')

    with sqlite3.connect('pulse.db') as connection:
        for event in flattened_events:
            date_object = datetime.strptime(event["startTime"],'%Y-%m-%dT%H:%M:%S.%f')
            formatted_date_str = date_object.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Inserting event {event['title']} from {event['club_name']} with date {formatted_date_str}")
            db_handling.insert_event_if_no_similar(conn=connection,event=(event['title'],formatted_date_str,event['artists'],event['venue_name'],event['venue_name'],"-1",f"https://ra.co/events/{event['id']}",""))