import requests
import pandas as pd
import os
from bs4 import BeautifulSoup
import lxml
from datetime import datetime,date

def scrape(dataframe):
    html = requests.get("http://www.fanfulla5a.it/2023/06/01/programma-giugno-2023/").content
    soup = BeautifulSoup(html, "lxml")

    events = soup.find_all('div', class_='siteorigin-widget-tinymce')
    events_list = []
    for event in events:
        event_dict = {}
        try:
            day = event.find('h3').text.split(' ')[1]
            day = datetime.strptime(f'{day} {datetime.now().month} {datetime.now().year}', '%d %m %Y')
        except Exception as e:
            print(e)
            continue
        event_dict["name"] = event.find('h4').text
        event_dict["location"] = 'Fanfulla 5/A Circolo Arci'
        time = event.find('span', class_='_4n-j fsl').text.split('dalle ore ')[1]
        time = datetime.strptime(time, '%H').strftime('%H:%M')
        event_dict["date_and_time"] = day.replace(hour=int(time.split(':')[0]), minute=int(time.split(':')[1]))
        event_dict["url"] = event.find_all('a')[-1]['href']
        events_list.append(event_dict)
    fanfulla_events = pd.DataFrame(events_list)
    return pd.concat([dataframe, fanfulla_events[['date_and_time', 'name', 'location', 'url']]])