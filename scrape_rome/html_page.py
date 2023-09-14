from datetime import datetime
from collections import defaultdict
from .custom_logger import logger

from .db_handling import return_events_by_month

def update_webpage(db_connection, file_to_write:str):

    events_in_db = return_events_by_month(db_connection,datetime.today())

    # group events by day
    events_by_day = defaultdict(list)
    for event in events_in_db:
        # Parse the date string and extract only the date part
        date = datetime.strptime(event[2], '%Y-%m-%d %H:%M:%S').date()
        # Add the event to the list of events for that date
        events_by_day[str(date)].append(event)

    # Print the events grouped by date
    html_content = UPPER_PART
    for date, events in sorted(events_by_day.items(),key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')):
        if datetime.strptime(date, '%Y-%m-%d').day >= datetime.today().day:
            
            html_content += f'''
                <!-- Day block -->
                <div>
                    <h5>{date}</h5>
                    <ul>'''

            # Add each link as a list item
            for event in sorted(events,key=lambda x: datetime.strptime(x[2], '%Y-%m-%d %H:%M:%S')):
                id,name,date,artists,organizer,location,price,link,descr = event
                html_content += f'''
                        <li>
                            <a href="{link}" target="_blank" db_id={id}>{organizer} || {name}</a>
                        </li>'''

            html_content += '''
                    </ul>
                </div>'''

    html_content += LOWER_PART
    
    # Write the HTML content to a file
    with open(file_to_write, 'w', encoding='utf-8') as file:
        logger.info("Writing html page!")
        file.write(html_content)

UPPER_PART = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
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
    h5,
    h6 {
        font-family: var(--font-main);
        color: var(--heading-color);
        line-height:1.1;
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
    }

    nav > p {
      margin: 0;
      padding: 10px 32px;
    }

    nav a {
        margin-right: 8px;
        font-size: .9em;
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
        /*padding: 5px 10px;
        /*background: var(--heading-color);*/
        color: var(--text-color);
        font-weight: 400;
        text-align:center;
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
    </style>
    </head>
    
    <body class="blog">
    <header>
        <a class="title" href="/">
            <h1>(((Pulse)))</h1>
        </a>
        <nav>
            <p><a href="/">Home</a> <a href="/next_month.html">Next Month</a> <a href="/past_events.html">Past Events</a></p>
        </nav>
    </header>

    <main>
        <ul class="blog-posts">
    """

LOWER_PART = """
        </ul>
    </main>

    <footer>
        <span>Your new favorite place to follow Rome's clubbing scene!</span>
    </footer>
    </body>
    </html>
    """