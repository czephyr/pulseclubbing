from datetime import datetime
from collections import defaultdict
import logging 
from .db_handling import return_valid_events_by_month

logger = logging.getLogger("mannaggia")

def update_webpage(db_connection, file_to_write:str, cronjob_date):

    events_in_db = return_valid_events_by_month(db_connection,cronjob_date)

    # Group events by day
    events_by_day = defaultdict(list)
    for event in events_in_db:
        # Parse the date string and extract only the date part
        date = datetime.strptime(event[2], '%Y-%m-%d %H:%M:%S').date()
        # Add the event to the list of events for that date
        events_by_day[str(date)].append(event)

    # Print the events grouped by date
    
    html_content = "" 
    if cronjob_date.date() == datetime.today().date():
        html_content = get_upper_part(is_next_month=False)
        day_to_compare = datetime.today().day
    else:
        html_content = get_upper_part(is_next_month=True)
        day_to_compare = datetime.today().replace(day=1).day
    for date, events in sorted(events_by_day.items(),key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')):
        if datetime.strptime(date, '%Y-%m-%d').day >= day_to_compare:
            
            html_content += f'''
                <!-- Day block -->
                <div class="divisor">
                    <h5>{datetime.strptime(date, '%Y-%m-%d').strftime('%A')} {datetime.strptime(date, '%Y-%m-%d').strftime('%d %B')}</h5>
                    <ul class="blog-posts">'''

            # Add each link as a list item
            for event in sorted(events,key=lambda x: datetime.strptime(x[2], '%Y-%m-%d %H:%M:%S')):
                id,name,date,artists,organizer,location,price,link,descr,is_valid,is_clubbing = event
                html_content += f'''
                        <li>
                            <a href="{link if link[:4] == 'http' else 'https://' + link}" target="_blank" db_id={id}><span class="underline-text">{organizer}</span> || {name}</a>
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
    with open(file_to_write, 'w', encoding='utf-8') as file:
        logger.info("Writing html page!")
        file.write(html_content)

def get_upper_part(is_next_month):
    next_month_button = '' if is_next_month else '<a href="/next_month">Next Month</a>'


    UPPER_PART = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5">
        <script defer data-domain="stase.it" src="https://stats.stase.it/js/script.js"></script>
        <style>


        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');

        :root {
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
        }

        body {
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
        }

        h1,
        h2,
        h3,
        h4,
        h6 {
            font-family: var(--font-main);
            color: var(--heading-color);
            line-height:1.1;
        }

        h5 {
            font-family: var(--font-main);
            color: #dd8521;
            font-size: 1.1em;
            line-height:0.9;
            margin-bottom: 6px; 
        }    

        a {
            color: var(--link-color);
            cursor: pointer;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        main {
            /*margin-top: 40px;*/
            margin-bottom: 20px;
            padding: 30px;
            border: 3px solid var(--text-color);
            border-top:none;
            line-height: 1.6;
        }

        nav {
          background: var(--text-color);
          text-transform: uppercase;
          letter-spacing: 0.3em;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        nav > p {
          margin: 0;
          padding: 10px 32px;
          flex-grow: 1;
        }

        nav > p:first-child {
          flex-grow: 1;
        }

        nav > p:last-child {
          flex-grow: 0;
        }

        nav a {
            margin-right: 8px;
            font-size: .8em;
            color:var(--background-color);
            text-decoration:none;
        }

        strong,
        b {
            color: var(--heading-color);
        }

        button {
            margin: 0;
            cursor: pointer;
        }

        table {
            width: 100%;
        }

        hr {
            border: 0;
            border-top: 1px dashed;
        }

        img {
            max-width: 100%;
        }

        footer {
            padding: 25px 0;
            text-align: center;
            opacity: 0.6;
        }

        .title:hover {
            text-decoration: none;
        }

        .title h1 {
            font-size: 2em;
            color: var(--text-color);
            font-weight: 400;
            text-align:center;
            margin-bottom: 15px;
        }

        .telegram-link {
            font-size: 0.8em; 
            text-align: center;
            margin-top: 0px;
            margin-bottom: 30px;
        }

        .inline {
            width: auto !important;
        }

        /* blog post list */
        ul.blog-posts {
            list-style-type: none;
            padding: unset;
        }

        ul.blog-posts li {
            display: flex;
            margin-bottom: 20px;
            flex-wrap:wrap;
        }

        ul.blog-posts li time {
            font-style: normal;
            font-size:.7em;
            font-weight:bold;
        }

        ul.blog-posts li span {
            flex: 0 0 100%;
        }

        ul.blog-posts li a:visited {
            color: var(--visited-color);
        }

        table {
            border-collapse: collapse;
        }

        table,
        th,
        td {
            border: 1px dashed var(--heading-color);
            padding: 10px;
        }

        .divisor {
            margin-bottom: 55px;
        }
        
        .underline-text {
            text-decoration: underline;
        }

        @media only screen and (max-width:767px) {
            main {
                padding: 20px;
                margin-top: 0px;
                margin-bottom: 10px;
            }

            ul.blog-posts li {
                flex-direction: column;
            }

            ul.blog-posts li span {
                flex: unset;
            }
        }

        @keyframes pulse {
            0% { content: "(((stase)))"; }
            20% { content: "((stase))"; }
            40% { content: "(stase)"; }
            60% { content: "stase"; }
            80% { content: "(stase)"; }
            100% { content: "((stase))"; }
        }

        h1::before {
            content: "(((stase)))";
            animation: pulse 2s infinite;
        }

        .link-with-arrow {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 30px;
            text-align: center;
        }

        .link-with-arrow a {
            display: inline-flex;
            align-items: center;
            color: var(--link-color);
            text-decoration: none;
            font-size: 1.1em;
            transition: color 0.3s ease;
        }

        .link-with-arrow a:hover {
            text-decoration: underline;
            color: var(--visited-color);
        }

        .link-with-arrow .arrow-icon {
            margin-left: 8px;
            transition: transform 0.3s ease;
        }

        .link-with-arrow a:hover .arrow-icon {
            transform: translateX(5px);
        }

        .home-link .arrow-icon {
            margin-left: 8px;
            margin-right: 0;
            transform: rotate(180deg);
        }

        .home-link a:hover .arrow-icon {
            transform: translateX(-5px) rotate(180deg);
        }
        </style>
        </head>
        
        <body class="blog">
        <header>
            <a class="title" href="/">
                <h1></h1>
            </a>
            <p class="telegram-link">Selected clubbing events in Rome. <a href="https://t.me/quindistase" target="_blank">Join the Telegram group: <span class="underline-text" style="color: #dd8521;">@quindistase</span></a></p>
            <nav>
                <p><a href="/">Home</a></p><p>""" + next_month_button +"""</oomp>
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