import sqlite3
from scrape_rome import db_handling

if __name__ == '__main__':
    with sqlite3.connect('pulse.db') as connection:
        db_handling.init_db(connection)