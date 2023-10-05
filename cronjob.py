import sqlite3
from scrape_rome import html_page, ig, ra, fanfulla, dice
from dotenv import load_dotenv
import logging

if __name__ == '__main__':
    load_dotenv()  

    logger = logging.getLogger("mannaggia")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(filename)s | %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    fh = logging.FileHandler('app.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    

    logger.addHandler(ch)
    logger.addHandler(fh)



    logger.info("-"*300)
    logger.info("Started new cronjob run")
    fanfulla.scrape()
    ra.scrape()
    ig.scrape(delta_days=3)
    dice.scrape()
    with sqlite3.connect('pulse.db') as connection:
        # care, event dates have to be strings
        html_page.update_webpage(connection,"www/gen_index.html")