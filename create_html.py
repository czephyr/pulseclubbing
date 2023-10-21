import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
from scrape_rome import html_page

if __name__ == '__main__':
    with sqlite3.connect('pulse.db') as connection:
        # care, event dates have to be strings
        html_page.update_webpage(connection,"www/gen_index.html",datetime.today())
        html_page.update_webpage(connection,"www/next_month.html",datetime.today()+relativedelta(months=1))
