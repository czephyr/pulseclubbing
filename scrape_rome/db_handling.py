from fuzzywuzzy.fuzz import token_sort_ratio
from datetime import datetime
from .custom_logger import logger

def init_db(conn):
    """initializes new db new db"""
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE events (id INTEGER PRIMARY KEY, name TEXT, date TEXT, artists TEXT, organizer TEXT, location TEXT, price REAL, link TEXT, raw_descr TEXT, is_valid INT DEFAULT 0)''')
    cursor.execute('''CREATE TABLE ig_posts (id INTEGER PRIMARY KEY, shortcode TEXT)''')
    conn.commit()

def delete_row_by_id(conn, id):
    """Delete row by id"""
    cur = conn.cursor()
    cur.execute("UPDATE events SET is_valid = 0 WHERE id=?", (id,))
    conn.commit()

def delete_row_by_name_and_organizer(conn, name, organizer):
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM events WHERE name=? AND organizer=?", (name, organizer,))
    row_exists = cur.fetchone()
    if row_exists:
        cur.execute("UPDATE events SET is_valid = 0 WHERE id=?", (str(row_exists[0]),))
        conn.commit()
        return row_exists[0]
    else:
        return -1

def insert_event_if_no_similar(conn, event):
    """Insert new event in db if no similar ones by organizer and name are found in the same date
       Returns None if successful"""
    cur = conn.cursor()
    name,date,_,organizer,_,_,_,_ = event
    try:
        datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
    except ValueError:
        logger.error(f"Error parsing date {date} for event {name} by {organizer}")
        return None
    day_events_query = "SELECT name, organizer FROM events WHERE date=?"
    cur.execute(day_events_query,(date,))
    rows = cur.fetchall()
    for db_event_name, db_event_organizer in rows:
        if db_event_name == name and db_event_organizer == organizer:
            # this event has been inserted already and its double scraped, 
            # no need to do anything here 
            logger.info(f"event {name} already inserted")
            return (db_event_name,db_event_organizer)
        if token_sort_ratio(db_event_name,name) > 75 and token_sort_ratio(db_event_organizer,organizer) > 75:
            # rejected for being too similar to one already present in db
            # on the same day
            logger.info(f"event {name} too similar to {db_event_name}")
            return (db_event_name,db_event_organizer)

    insert_query = "INSERT INTO events(name,date,artists,organizer,location,price,link,raw_descr) VALUES(?,?,?,?,?,?,?,?)"
    cur.execute(insert_query, event)
    logger.info("inserted successfully")
    conn.commit()
    return None

def is_igpost_shortcode_in_db(conn, shortcode):
    """Return True when the passed shortcode is already in the db"""
    cur = conn.cursor()
    shortcode_query = "SELECT * FROM ig_posts WHERE shortcode=?"
    cur.execute(shortcode_query,(shortcode,))
    rows = cur.fetchall()
    return len(rows) > 0

def return_events_by_month(conn, date):
    """Insert new event in db if no similar ones by organizer and name are found in the same date"""
    cur = conn.cursor()
    day_events_query = "SELECT * FROM events WHERE is_valid = 1 AND date LIKE ? || '-' || ? || '-%'"
    cur.execute(day_events_query, (date.strftime('%Y'), date.strftime('%m')))
    return cur.fetchall()

