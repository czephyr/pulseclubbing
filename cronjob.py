from scrape_rome import html_page, ig
import sqlite3

if __name__ == '__main__':
    # THIS NEEDS TO BE REWRITTEN TO RETURN A LIST NOT A DF? Can return a df if too difficult
    # just care about the event input of insert_event_if_no_similar
    # df = pd.DataFrame()
    # df = fanfulla.scrape(df)
    # df = ra.scrape(df)
    scraped_events = []
    ig.scrape_and_insert(ig.USERNAMES_TO_SCRAPE)
    with sqlite3.connect('pulse.db') as connection:
        # care, event dates have to be strings
        html_page.update_webpage(connection,"www/gen_index.html")