import pandas as pd
from datetime import datetime,date
from scrape_rome import fanfulla, ra

def merge_events(scraped_df,month_name):
    # TODO: gestione dei file per mese????
    # current = pd.read_csv(f'data/{month_name}.csv')
    current = pd.read_csv(f'data/events.csv')
    concat = pd.concat([current, scraped_df])
    concat.drop_duplicates().to_csv(f'data/events.csv',index=False)
    #os.remove('data/new.csv')

def update_webpage(month_name,file_to_write:str):
    df = pd.read_csv(f'data/events.csv')

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
    for time, group in df.groupby('date_and_time'):
        current_date = date.today()

        # Compare the dates
        if datetime.strptime(time, '%Y-%m-%d %H:%M:%S').date() >= current_date and datetime.strptime(time, '%Y-%m-%d %H:%M:%S').date().month == current_date.month:
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
    with open(file_to_write, 'w') as file:
        file.write(html_content)

if __name__ == '__main__':
    df = pd.DataFrame()
    df = fanfulla.scrape(df)
    df = ra.scrape(df)
    current_month_name = datetime.now().strftime('%B').lower()
    merge_events(df, current_month_name)
    update_webpage(current_month_name,"www/gen_index.html")