from datetime import datetime, timedelta, date
from collections import defaultdict
import logging 
from .db_handling import return_valid_events_by_date
import paramiko
import os
from dotenv import load_dotenv

load_dotenv()
IS_LOCAL = os.getenv("RUN_LOCALLY") == 'true'
logger = logging.getLogger("mannaggia")


def write_ssh(html:str, file_path:str):
    private_key = paramiko.RSAKey.from_private_key_file(os.getenv("SSH_KEY_TO_DIGITALOCEAN"))
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(os.getenv("DIGITALOCEAN_IP"), port=os.getenv("DIGITALOCEAN_PORT"), username=os.getenv("DIGITALOCEAN_USERNAME"), pkey=private_key)
    sftp = client.open_sftp()

    remote_file_path = f'/home/pulseclubbing/{file_path}'

    with sftp.open(remote_file_path, 'w') as remote_file:
        logger.info(f"Writing {file_path} page remotely!")
        remote_file.write(html)
    sftp.close()
    client.close()



def update_webpage(db_connection, file_to_write:str, cronjob_date):

    if file_to_write == "www/gen_index.html":
        today = cronjob_date.date()
    else:
        today = cronjob_date.replace(day=1).date()
    tomorrow = today + timedelta(days=1)

    start_date, end_date = get_display_date_range(today)
    events_in_db = return_valid_events_by_date(db_connection, start_date, end_date)

    # Group events by day
    events_by_day = defaultdict(list)
    for event in events_in_db:
        # Parse the date string and extract only the date part
        date = datetime.strptime(event[2], '%Y-%m-%d %H:%M:%S').date()
        # Add the event to the list of events for that date
        events_by_day[str(date)].append(event)

    html_content = "" 
    if file_to_write == "www/gen_index.html":
        html_content = get_upper_part(is_next_month=False)
    else:
        html_content = get_upper_part(is_next_month=True)

    # Print the events grouped by date
    for date_str, events in sorted(events_by_day.items(),key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')):
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        if today <= date_obj <= end_date:
            if date_obj == today and file_to_write == "www/gen_index.html":
                day_display = "Today"
            elif date_obj == tomorrow and file_to_write == "www/gen_index.html":
                day_display = "Tomorrow"
            else:
                day_display = date_obj.strftime('%A %d %B')
            
            html_content += f'''
                <!-- Day block -->
                <div class="divisor">
                    <h5>{day_display}</h5>
                    <ul class="blog-posts">'''

            # Add each link as a list item
            for event in sorted(events,key=lambda x: datetime.strptime(x[2], '%Y-%m-%d %H:%M:%S')):
                id,name,date,artists,organizer,location,price,link,descr,is_valid,is_clubbing,timestamp, *rest = event
                html_content += f'''
                        <li>
                            <a href="{link if link[:4] == 'http' else 'https://' + link}" target="_blank" db_id={id}>» <span class="underline-text">{organizer}</span> || {name}</a>
                        </li>'''

            html_content += '''
                    </ul>
                </div>'''
    
    if file_to_write == "www/gen_index.html":
        html_content += f'''
            <div class="link-with-arrow">
                <a href="/next_month">
                    See Next Month
                    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                        <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                </a>
            </div>'''
    else:
        html_content += f'''
        <div class="link-with-arrow home-link">
            <a href="/">
                <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
                Back to this Month
            </a>
        </div>'''

    html_content += LOWER_PART
    
    # Write the HTML content to a file
    if not IS_LOCAL:
        write_ssh(html=html_content, file_path=file_to_write)
    else:
        with open(file_to_write, 'w', encoding='utf-8') as file:
            file.write(html_content)

def get_display_date_range(today):
    """
    Calculate the start and end dates for event display based on the current date.
    
    - If the current date is within the last week of the month, extend the end date to include some days of the next month.
    - Otherwise, set the end date to the last day of the current month or further based on specific logic.
    """
    # Start date for fetching events is today
    start_date = today

    # Move to the first day of the next month, then find the last day of the current month
    first_day_of_next_month = today.replace(day=28) + timedelta(days=4)
    first_day_of_next_month = first_day_of_next_month.replace(day=1)
    last_day_of_current_month = first_day_of_next_month - timedelta(days=1)
    
    # Check if today is within the last week of the month
    is_last_week = today > last_day_of_current_month - timedelta(days=7)
    
    if is_last_week:
        # If within the last week, decide how far into the next month to show events
        # This example extends to the next Sunday, or you can choose another logic
        next_sunday = today + timedelta(days=(6-today.weekday()+1) % 7)
        # Ensure the end date is at least next Sunday, or the last day of the next month if next Sunday is in the current month
        if next_sunday.month == today.month:
            # This means next Sunday is still within the current month, so pick a date from the next month
            end_date = last_day_of_current_month + timedelta(days=7)  # Arbitrary extension into the next month
        else:
            end_date = next_sunday
    else:
        # Not within the last week, end date is the last day of the current month
        end_date = last_day_of_current_month

    return start_date, end_date


def get_upper_part(is_next_month):

    if is_next_month:
        nav_content = '<p><a href="/">Back Home</a></p>'
    else:
        nav_content = '<p><a href="/next_month">Next Month</a></p>'


    UPPER_PART = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5">
        <script defer data-domain="stase.it" src="https://stats.stase.it/js/script.js"></script>
        <style>


        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');

        :root {{
            --width: 800px;
            --font-main: 'Fira Code', monospace;
            --font-secondary: 'Fira Code', monospace;
            --font-scale: 1.3em;
            --background-color: #000;
            --heading-color: #0099FF;
            --text-color: #0099FF;
            --link-color: #0099FF;
            --visited-color: #0088CC;
            --suggested-event-color: #9C27B0;
        }}

        body {{
            font-family: var(--font-secondary);
            font-size: var(--font-scale);
            margin: auto;
            padding: 20px;
            max-width: var(--width);
            text-align: left;
            background-color: var(--background-color);
            word-wrap: break-word;
            overflow-wrap: break-word;
            line-height: 1.5;
            color: var(--text-color);
        }}

        h1,
        h2,
        h3,
        h4,
        h6 {{
            font-family: var(--font-main);
            color: var(--heading-color);
            line-height:1.1;
        }}

        h5 {{
            font-family: var(--font-main);
            color: #dd8521;
            font-size: 1.1em;
            line-height:0.9;
            margin-bottom: 6px; 
        }}    

        a {{
            color: var(--link-color);
            cursor: pointer;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        main {{
            /*margin-top: 40px;*/
            margin-bottom: 20px;
            padding: 30px;
            border: 3px solid var(--text-color);
            border-top:none;
            line-height: 1.6;
        }}

        nav {{
          background: var(--text-color);
          text-transform: uppercase;
          letter-spacing: 0.3em;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }}

        nav > p {{
          margin: 0;
          padding: 10px 32px;
          flex-grow: 1;
        }}

        nav > p:first-child {{
          flex-grow: 1;
        }}

        nav > p:last-child {{
          flex-grow: 0;
        }}

        nav a {{
            margin-right: 8px;
            font-size: .8em;
            color:var(--background-color);
            text-decoration:none;
        }}

        strong,
        b {{
            color: var(--heading-color);
        }}

        button {{
            margin: 0;
            cursor: pointer;
        }}

        table {{
            width: 100%;
        }}

        hr {{
            border: 0;
            border-top: 1px dashed;
        }}

        img {{
            max-width: 100%;
        }}

        footer {{
            padding: 25px 0;
            text-align: center;
            opacity: 0.6;
        }}

        .title:hover {{
            text-decoration: none;
        }}

        .title h1 {{
            font-size: 2em;
            color: var(--text-color);
            font-weight: 400;
            text-align:center;
            margin-bottom: 15px;
        }}

        .telegram-link {{
            font-size: 0.8em; 
            text-align: center;
            margin-top: 0px;
            margin-bottom: 30px;
        }}

        .inline {{
            width: auto !important;
        }}

        /* blog post list */
        ul.blog-posts {{
            list-style-type: none;
            padding: unset;
        }}

        ul.blog-posts li {{
            display: flex;
            margin-bottom: 20px;
            flex-wrap:wrap;
        }}

        ul.blog-posts li time {{
            font-style: normal;
            font-size:.7em;
            font-weight:bold;
        }}

        ul.blog-posts li span {{
            flex: 0 0 100%;
        }}

        ul.blog-posts li a:visited {{
            color: var(--visited-color);
        }}

        table {{
            border-collapse: collapse;
        }}

        table,
        th,
        td {{
            border: 1px dashed var(--heading-color);
            padding: 10px;
        }}

        .divisor {{
            margin-bottom: 55px;
        }}
        
        .underline-text {{
            text-decoration: underline;
        }}

        @media only screen and (max-width:767px) {{
            main {{
                padding: 20px;
                margin-top: 0px;
                margin-bottom: 10px;
            }}

            ul.blog-posts li {{
                flex-direction: column;
            }}

            ul.blog-posts li span {{
                flex: unset;
            }}
        }}

        @keyframes pulse {{
            0% {{ content: "(((stase)))"; }}
            20% {{ content: "((stase))"; }}
            40% {{ content: "(stase)"; }}
            60% {{ content: "stase"; }}
            80% {{ content: "(stase)"; }}
            100% {{ content: "((stase))"; }}
        }}

        h1::before {{
            content: "(((stase)))";
            animation: pulse 2s infinite;
        }}

        .link-with-arrow {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 30px;
            text-align: center;
        }}

        .link-with-arrow a {{
            display: inline-flex;
            align-items: center;
            color: var(--link-color);
            text-decoration: none;
            font-size: 1.1em;
            transition: color 0.3s ease;
        }}

        .link-with-arrow a:hover {{
            text-decoration: underline;
            color: var(--visited-color);
        }}

        .link-with-arrow .arrow-icon {{
            margin-left: 8px;
            transition: transform 0.3s ease;
        }}

        .link-with-arrow a:hover .arrow-icon {{
            transform: translateX(5px);
        }}

        .home-link .arrow-icon {{
            margin-left: 8px;
            margin-right: 0;
            transform: rotate(180deg);
        }}

        .home-link a:hover .arrow-icon {{
            transform: translateX(-5px) rotate(180deg);
        }}
        </style>
        </head>
        
        <body class="blog">
        <header>
            <a class="title" href="/">
                <h1></h1>
            </a>
            <p class="telegram-link">Selected clubbing events in Rome.</br><a href="https://t.me/quindistase" target="_blank">Join the Telegram group: <span class="underline-text" style="color: #dd8521;">@quindistase</span></a></p>
            <nav>
                {nav_content}
            </nav>
        </header>

        <main>
        """
    return UPPER_PART


LOWER_PART = """
    </main>

    <footer>
        <span>Your new favorite place to follow Rome's clubbing scene!</span>
    </footer>
    </body>
    </html>
    """