from scrape_rome import html_page, ig, ra, fanfulla
from scrape_rome.db_handling import delete_row_by_id
import sqlite3

if __name__ == '__main__':
    fanfulla.scrape()
    ra.scrape()
    # ig.scrape_and_insert(ig.USERNAMES_TO_SCRAPE)
    with sqlite3.connect('pulse.db') as connection:
        # care, event dates have to be strings
        html_page.update_webpage(connection,"www/gen_index.html")