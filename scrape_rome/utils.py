from ftfy import fix_text
from unidecode import unidecode
import re
from fuzzywuzzy import fuzz
import logging
from datetime import datetime

logger = logging.getLogger("mannaggia")

def clean_text(text, source='', ):
    # write documentation for this function
    """
    ### Clean text in various ways depending on the source.
    
    #### Args:
        text (str): Text to be cleaned
        source (str, optional): Source of the text. Defaults to ''. Possible values: 'resident_advisor', 'comparison'.

    #### Returns:
        str: Cleaned text
    """
    text = fix_text(text)
    text = re.sub(r'\s+', ' ', text)
    if source == 'resident_advisor':
        text = unidecode(text)
    if source == 'comparison':
        text = text.lower()
        text = unidecode(text) # This goes before the removal of special characters because it removes accents
        text = re.sub(r'[^a-zA-Z0-9 ]', '', text) # Delete all special characters a part from the spaces
    text = re.sub(r'(?<!\d)-(?!\d)', ' ', text) # Delete all special characters a part from the ones dashes that are preceded and followed by numbers
    return text

def check_similarity(event, rows):
    """
    ### Returns True if the event is too similar to one already in the db for the same day
    
    #### Args:
        event (tuple): Event to be checked
        rows (list): List of tuples of events already in the db for the same day

    #### Returns:
        bool: True if the event is too similar to one already in the db for the same day
    """
    name,date,_,organizer,_,_,_,_ = event
    if not rows:
        return False
    for db_event_name, db_event_organizer in rows:
        logger.debug(f"Comparing event {db_event_name} and {name}")
        if clean_text(db_event_organizer) == clean_text(organizer) and clean_text(db_event_name) == clean_text(name):
            return True
        elif fuzz.token_sort_ratio(clean_text(db_event_name),clean_text(name)) > 75 and fuzz.token_sort_ratio(clean_text(db_event_organizer),clean_text(organizer)) > 75:
            return True
        elif fuzz.token_sort_ratio(clean_text(db_event_name),clean_text(name)) > 90:
            return True
        elif fuzz.token_sort_ratio(clean_text(db_event_organizer),clean_text(organizer)) > 90:
            return True
        else:
            return False
        
        # code to save the full json appending it to a file called skipped.txt, adding at the top of the json the date of the scraping without hours
                                # and then continue
                                # create file if not exists
def skipped_handling(response):
    """
    #### Save the full json appending it to a file called skipped.txt

    #### Args:
        response (json): Response from OpenAI API

    #### Returns:
        None
    """
    with open('skipped.txt', 'a+') as f: # If file exists, append to it, else create it
        f.seek(0) # Go to the beginning of the file
        data = f.read(100)  # read the first 100 bytes
        if len(data) > 0: # if the file is not empty
            f.write("\n") # write a newline
        f.write(f"{'-'*30}{datetime.now().strftime('%Y-%m-%d')}{'-'*30}\n{response}") # Write the data along with the json
    return None