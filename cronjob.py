import argparse
import sqlite3
from scrape_rome import html_page, ig, ra, fanfulla, dice, trenta_formiche, reveries
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import logging
import arrow
import os
from telegram import Bot

if __name__ == '__main__':
    load_dotenv()

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run specified scrapers or update HTML based on input.")
    parser.add_argument("--only", nargs='+', help="Specify one or more tasks to run: fanfulla, trenta_formiche, ra, ig, dice, html")
    args = parser.parse_args()

    # Initialize an empty set for tasks to run if --only is specified, otherwise None
    tasks_to_run = set(args.only) if args.only else None

    # Set up logging
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

    utc = arrow.utcnow()
    utc.shift(hours=+2)
    date = utc.format('YYYY-MM-DD HH:mm')
    logger.info("-"*300)
    logger.info(f"Started new cronjob run {date}")

    # Define a helper function to check if a task should run
    def should_run(task_name):
        # Run if tasks_to_run is None (meaning --only wasn't used) or task_name is in tasks_to_run
        return tasks_to_run is None or task_name in tasks_to_run

    Bot(token=os.getenv("TELEGRAM_TOKEN")).send_message(chat_id=-1002041332676,text="testtesttest")

    # Execute tasks based on the provided arguments or run all if no --only
    if should_run("fanfulla"):
        try:
            fanfulla.scrape()
        except Exception as e:
            logger.error('SIGNIFICANT ERROR IN SCRAPING FANFULLA:', e)

    if should_run("trenta_formiche"):
        try:
            trenta_formiche.scrape()
        except Exception as e:
            logger.error('SIGNIFICANT ERROR IN SCRAPING TRENTA FORMICHE:', e)

    if should_run("ra"):
        try:
            ra.scrape()
        except Exception as e:
            logger.error('SIGNIFICANT ERROR IN SCRAPING RA:', e)

    if should_run("ig"):
        try:
            ig.scrape(delta_days=5)
        except Exception as e:
            logger.error('SIGNIFICANT ERROR IN SCRAPING IG:', e)

    if should_run("dice"):
        try:
            dice.scrape()
        except Exception as e:
            logger.error('SIGNIFICANT ERROR IN SCRAPING DICE:', e)

    if should_run("reveries"):
        try:
            reveries.scrape()
        except Exception as e:
            logger.error('SIGNIFICANT ERROR IN SCRAPING REVERIES:', e)

    if should_run("html"):
        with sqlite3.connect('pulse.db') as connection:
            html_page.update_webpage(connection, "www/gen_index.html", datetime.today())
            html_page.update_webpage(connection, "www/next_month.html", datetime.today().replace(day=1) + relativedelta(months=1))
