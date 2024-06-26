from ftfy import fix_text
from unidecode import unidecode
import re
from fuzzywuzzy import fuzz
import logging
import os
import requests

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
        # Variables holding cleane
        clean_db_event_name = clean_text(db_event_name, source='comparison')
        clean_name = clean_text(name, source='comparison')
        clean_db_event_organizer = clean_text(db_event_organizer, source='comparison')
        clean_organizer = clean_text(organizer, source='comparison')
        if clean_db_event_name == clean_name and clean_db_event_organizer == clean_organizer:
            logger.info(f"Event {name} already present in db")
            return True
        name_tsr = fuzz.token_sort_ratio(clean_db_event_name, clean_name)
        org_tsr = fuzz.token_sort_ratio(clean_db_event_organizer, clean_organizer)
        logger.debug(f"Name tsr: {name_tsr} and org tsr: {org_tsr}")
        if name_tsr > 75 or org_tsr > 75:
            logger.info(f"Event {name} too similar to one already present in db")
            return True
    return False

def get_insta_shortcode(insta_link):
    return re.search(r"instagram\.com/p/([^/]+)/?", insta_link).group(1)

def check_date_format(date:str):
    format = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
    return re.match(format, date)

def send_tg_log(text):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = "-1002041332676"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    response = requests.post(url, data=data)