from ftfy import fix_text
from unidecode import unidecode
import re

def clean_text(text, source=''):
    text = fix_text(text)
    text = re.sub(r'\s+', ' ', text)
    if source == 'scraper':
        text = unidecode(text)
        text = text.lower() # Since gpt better understands uppercase letters, I'll leave them
    text = re.sub(r'(?<!\d)-(?!\d)', ' ', text) # Delete all special characters a part from the ones dashes that are preceded and followed by numbers
    return text