import logging
from fuzzywuzzy.fuzz import token_sort_ratio
from datetime import datetime
from . import utils
from pydantic import BaseModel

class Event(BaseModel):
    name: str
    date: str
    artists: str
    organizer: str
    location: str
    price: str
    link: str
    raw_descr: str

logger = logging.getLogger("mannaggia")

def init_db(conn):
    """initializes new db new db"""
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, name TEXT, date TEXT, artists TEXT, organizer TEXT, location TEXT, price REAL, link TEXT, raw_descr TEXT, is_valid INT DEFAULT 1, is_clubbing INT DEFAULT 1)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ig_posts (id INTEGER PRIMARY KEY, shortcode TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS visit_stats (id INTEGER PRIMARY KEY, date TEXT, count INTEGER)''')
    conn.commit()

def insert_visits(conn, date, count):
    cur = conn.cursor()
    cur.execute("INSERT INTO visit_stats (date, count) VALUES (?, ?)", (date, count))
    conn.commit()

def delete_row_by_id(conn, id):
    """Delete row by id"""
    cur = conn.cursor()
    cur.execute("UPDATE events SET is_valid = 0 WHERE id=?", (id,))
    conn.commit()

def visits_stats(conn):    
    cur = conn.cursor()
    cur.execute("SELECT * FROM visit_stats ORDER BY date LIMIT 7")
    this_week = cur.fetchall()
    return [(date,visits) for (id,date,visits) in this_week]

def delete_row_by_name_and_organizer(conn, name, organizer):
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM events WHERE name=? AND organizer=?", (name, organizer,))
    row_exists = cur.fetchone()
    if row_exists:
        cur.execute("UPDATE events SET is_valid = 0 WHERE id=?", (str(row_exists[0]),))
        conn.commit()
        return row_exists[0]
    else:
        return None

def insert_event_if_no_similar(conn, event):
    """Insert new event in db if no similar ones by organizer and name are found in the same date
       Returns None if successful"""
    cur = conn.cursor()
    name,date,artists,organizer,location,price,link,raw_descr = event
    try:
        date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
    except ValueError:
        logger.error(f"Error parsing date {date} for event {name} by {organizer}")
        return None
    day_events_query = "SELECT name, organizer FROM events WHERE is_valid = 1 and date LIKE ? || '-' || ? || '-' || ? || ' %'"
    cur.execute(day_events_query,(date.strftime('%Y'), date.strftime('%m'), date.strftime('%d'),))
    rows = cur.fetchall()
    if utils.check_similarity(event, rows):
        logger.info(f"Event {name} too similar to one already present in db")
        return None
    else:
        insert_query = "INSERT INTO events(name,date,artists,organizer,location,price,link,raw_descr) VALUES(?,?,?,?,?,?,?,?)"
        cur.execute(insert_query, event)
        rows = cur.fetchall()
        logger.info("inserted successfully")
        conn.commit()
        return True

def add_igpost_shortcode(conn, shortcode):
    """Return True when the passed shortcode gets inserted in the db"""
    cur = conn.cursor()
    shortcode_query = "INSERT INTO ig_posts (shortcode) VALUES (?)"
    cur.execute(shortcode_query,(shortcode,))
    rows = cur.fetchall()
    return len(rows) > 0

def is_igpost_shortcode_in_db(conn, shortcode):
    """Return True when the passed shortcode is already in the db"""
    cur = conn.cursor()
    shortcode_query = "SELECT * FROM ig_posts WHERE shortcode=?"
    cur.execute(shortcode_query,(shortcode,))
    rows = cur.fetchall()
    return len(rows) > 0

def return_valid_events_by_month(conn, date):
    """Return valid events from the db which are in the same month as the date passed"""
    cur = conn.cursor()
    day_events_query = "SELECT * FROM events WHERE is_valid = 1 AND date LIKE ? || '-' || ? || '-%'"
    cur.execute(day_events_query, (date.strftime('%Y'), date.strftime('%m')))
    return cur.fetchall()

def update_is_clubbing(conn, event_id, is_clubbing):
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM events WHERE id=?", (event_id,))
    row_exists = cur.fetchone()
    if row_exists:
        cur.execute("UPDATE events SET is_clubbing = ? WHERE id=?", (str(is_clubbing),str(row_exists[0]),))
        conn.commit()
        return row_exists[0]
    else:
        return None
