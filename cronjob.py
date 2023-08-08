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
    current_month_n = datetime.now().strftime('%-m')
    df = pd.read_csv(f'data/{current_year}/{current_month_n}.csv', parse_dates=['date_and_time'])

    html_content = '''<!DOCTYPE html>
    <html lang="en">

    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>Links of the Month</title>

        <!-- Latest compiled and minified CSS -->
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">
    </head>

    <body>
        <h1 class="mt-4 mb-4">Links of the Month</h1>
        <div class="container">'''

    # Iterate over the unique dates and group the events by date
    for time, group in df.groupby(df['date_and_time'].dt.date):
        current_date = date.today()

        # Compare the dates
        if time.day >= current_date.day and time.month == current_date.month and time.year == current_date.year:
            # Format the date as "Month day" (e.g., "August 4th")
            formatted_date = pd.to_datetime(time).strftime('%B %d')
            html_content += f'''
                <!-- Day block -->
                <div class="container">
                    <h5 class="mb-2">{formatted_date}</h5>
                    <ul class="list-group mb-3">'''

            # Add each link as a list item
            for _, row in group.iterrows():
                html_content += f'''
                        <li class="list-group-item">
                            <a href="{row['url']}">{row['location']} - {row['name']}</a>
                        </li>'''

            html_content += '''
                    </ul>
                </div>
                <!-- End of day block -->'''

    # Complete the HTML content
    html_content += '''
        </div>
        <!-- Latest compiled and minified JavaScript -->
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js"></script>
    </body>
    </html>'''

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