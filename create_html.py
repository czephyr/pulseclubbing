import sqlite3
from scrape_rome import html_page

if __name__ == '__main__':
    with sqlite3.connect('pulse.db') as connection:
        # care, event dates have to be strings
        html_page.update_webpage(connection,"www/gen_index.html")
