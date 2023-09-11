from fuzzywuzzy.fuzz import token_sort_ratio

def init_db(conn):
    """initializes new db new db"""
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE events (id INTEGER PRIMARY KEY, name TEXT, date TEXT, artists TEXT, organizer TEXT, location TEXT, price REAL, link TEXT)''')
    cursor.execute('''CREATE TABLE ig_posts (id INTEGER PRIMARY KEY, shortcode TEXT)''')
    conn.commit()

def insert_event_if_no_similar(conn, event):
    """Insert new event in db if no similar ones by organizer and name are found in the same date
       Returns None if successful"""
    cur = conn.cursor()

    name,date,_,organizer,_,_,_ = event
    # date = date.strftime("%Y/%M/%D, %H:%M:%S") not needed?

    day_events_query = "SELECT name, organizer FROM events WHERE date=?"
    cur.execute(day_events_query,(date,))
    rows = cur.fetchall()
    for db_event_name, db_event_organizer in rows:
        if db_event_name == name and db_event_organizer == organizer:
            # this event has been inserted already and its double scraped, 
            # no need to do anything here 
            return (db_event_name,db_event_organizer)
        if token_sort_ratio(db_event_name,name) > 75:
            # TODO: send to telegram users a log about which event 
            # was rejected for being too similar to one already present in db
            # on the same day
            return (db_event_name,db_event_organizer)
        elif token_sort_ratio(db_event_organizer,organizer) > 75:
            # TODO: send to telegram users a log about which event 
            # was rejected for being too similar to one already present in db
            # on the same day
            return (db_event_name,db_event_organizer)

    insert_query = "INSERT INTO events(name,date,artists,organizer,location,price,link) VALUES(?,?,?,?,?,?,?)"
    cur.execute(insert_query, event)
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

    day_events_query = "SELECT * FROM events WHERE date LIKE '?-?-%'"
    cur.execute(day_events_query,(date.strftime('%Y'),date.strftime('%M')))
    return cur.fetchall()

