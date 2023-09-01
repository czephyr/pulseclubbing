import pandas as pd
import os
from datetime import datetime,date
from scrape_rome import fanfulla, ra

def merge_events(scraped_df):
    current_year = datetime.now().strftime('%Y')
    scraped_df['date_and_time'] = pd.to_datetime(scraped_df['date_and_time'])
    for month, scraped_by_month in scraped_df.groupby(scraped_df['date_and_time'].dt.month):
        stored_df = pd.read_csv(f'data/{current_year}/{month}.csv',parse_dates=["date_and_time"])
        concat = pd.concat([stored_df, scraped_by_month])
        concat.drop_duplicates(inplace=True)
        concat.to_csv(f'data/{current_year}/{month}.csv',index=False)

def update_webpage(file_to_write:str):
    current_year = datetime.now().strftime('%Y')
    current_month_n = int(datetime.now().strftime('%m'))
    df = pd.read_csv(f'data/{current_year}/{current_month_n}.csv', parse_dates=['date_and_time'])

    html_content = """
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
            <h1>Pulse.</h1>
        </a>
        <nav>
            <p><a href="/">Home</a> <a href="/next_month.html">Next Month</a> <a href="/past_events.html">Past Events</a></p>
        </nav>
    </header>

    <main>
        <ul class="blog-posts">
    """

    # Iterate over the unique dates and group the events by date
    for time, group in df.groupby(df['date_and_time'].dt.date):
        current_date = date.today()

        # Compare the dates
        if time >= current_date and time.month == current_date.month and time.year == current_date.year:
            # Format the date as "Month day" (e.g., "August 4th")
            formatted_date = pd.to_datetime(time).strftime('%B %d')
            html_content += f'''
                <!-- Day block -->
                <div>
                    <h5>{formatted_date}</h5>
                    <ul>'''

            # Add each link as a list item
            for _, row in group.iterrows():
                html_content += f'''
                        <li>
                            <a href="{row['url']}" target="_blank">{row['location']} - {row['name']}</a>
                        </li>'''

            html_content += '''
                    </ul>
                </div>'''


    html_content += """
        </ul>
    </main>

    <footer>
        <span>Your new favorite place to follow Rome's clubbing scene!</span>
    </footer>
    </body>
    </html>
    """
    
    # Write the HTML content to a file
    with open(file_to_write, 'w', encoding='utf-8') as file:
        file.write(html_content)
    
if __name__ == '__main__':
    if not os.path.exists('data/events.csv'):
        empty_df = pd.DataFrame(columns=['date_and_time', 'name', 'location', 'url'])
        empty_df.to_csv('data/events.csv', index=False)
    df = pd.DataFrame()
    df = fanfulla.scrape(df)
    df = ra.scrape(df)
    merge_events(df)
    update_webpage("www/gen_index.html")