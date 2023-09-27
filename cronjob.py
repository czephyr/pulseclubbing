import sqlite3
from scrape_rome import html_page, ig, ra, fanfulla, dice
from scrape_rome.custom_logger import logger
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()  

    logger.info("-"*300)
    logger.info("Started new cronjob run")
    fanfulla.scrape()
    ra.scrape()
    ig.scrape(delta_days=3)
    dice.scrape()
    with sqlite3.connect('pulse.db') as connection:
        # care, event dates have to be strings
        html_page.update_webpage(connection,"www/gen_index.html")