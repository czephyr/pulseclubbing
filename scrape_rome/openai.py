import openai
import logging

logger = logging.getLogger("mannaggia")

def create_prompt(description, username='', link=''):
    messages = []
    
    # System instruction message
    messages.append({
        "role": "system",
        "content": """
        You're tasked with extracting event information from a caption.
        The output should be a valid JSON, starting with { and ending with }.
        The events you should focus on are primarily clubbing events in Rome.
        If the event is related to theatre, cinema, film festival, or any non-musical event, YOU MUST return an empty JSON {}. Otherwise, extract the following:
        - date: Format as %Y-%m-%d %H:%M:%S (remember that year is 2023 unless explicitly mentioned)
        - name: Name of the event
        - artists: Names of performing artists, separated by commas (they could be written as instagram usernames, in case try to prettify them)
        - location: Venue of the event
        - price: Ticket cost or 'Free' if explicitly mentioned
        - organizer: Instagram username of the account posting the event
        - link: URL to the Instagram profile posting the event, or dice.fm link

        Examples of non-clubbing events include: theatre shows, cinema nights, film festivals. For these, return an empty JSON {}.
        """
    })
    
    # If provided, append the username and link as separate user messages
    if username:
        messages.append({
            "role": "user",
            "content": f"Organizer: {username}"
        })
    if link:
        messages.append({
            "role": "user",
            "content": f"Link: {link}"
        })
    
    # Main event description
    messages.append({
        "role": "user",
        "content": f"Caption: '{description}'"
    })

    return messages

def get_event_info(description, source, key, username='', link=''):
    # At the moment, source is not used but it could be helpful in the future to handle different prompts
    openai.api_key = key
    
    prompt_messages = create_prompt(description, username=username, link=link)
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt_messages
    )
    
    # Extract the text from the assistant's response
    return response.choices[0].message['content'].strip()