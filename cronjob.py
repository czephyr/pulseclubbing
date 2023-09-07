import pandas as pd
import os
from datetime import datetime,date
from scrape_rome import fanfulla, ra, html_page, db_handling
import sqlite3


if __name__ == '__main__':
    # THIS NEEDS TO BE REWRITTEN TO RETURN A LIST NOT A DF
    # df = pd.DataFrame()
    # df = fanfulla.scrape(df)
    # df = ra.scrape(df)
    scraped_events = []
    with sqlite3.connect('pulse.db') as connection:
        # care, event dates have to be strings
        for event in scraped_events:
            db_handling.insert_event(connection, event)
        html_page.update_webpage(connection,"www/gen_index.html")