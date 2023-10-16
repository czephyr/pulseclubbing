import os
import re
from datetime import datetime
from scrape_rome import db_handling
import sqlite3

INPUT_DIR = "/var/log/nginx/"
current_date = datetime.now().strftime('%Y-%m-%d')
lineformat = re.compile(r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\/[1-2]\.[0-9]")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["])""", re.IGNORECASE)

logfile = open(os.path.join(INPUT_DIR, "access.log"))

visit_counter = 0
for l in logfile.readlines():
    data = re.search(lineformat, l)
    if data:
        datadict = data.groupdict()
        if datadict["url"] == "/ ":
            # ip = datadict["ipaddress"]
            # datetimestring = datadict["dateandtime"]
            # url = datadict["url"]
            # bytessent = datadict["bytessent"]
            # referrer = datadict["refferer"]
            # useragent = datadict["useragent"]
            # status = datadict["statuscode"]
            # method = data.group(6)
            
            visit_counter += 1

            # print(ip, \
            #     datetimestring, \
            #     url, \
            #     bytessent, \
            #     referrer, \
            #     useragent, \
            #     status, \
            #     method)

logfile.close()

with sqlite3.connect('pulse.db') as connection:
    db_handling.insert_visits(connection, current_date, visit_counter)