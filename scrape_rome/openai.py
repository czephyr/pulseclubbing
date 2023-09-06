import openai

PROMPT_CONTEXT = """
È il 2023, il messaggio che segue delimitato dalle virgolette è la caption di un post descrivente un evento.
Raccogli le seguenti informazioni dalla caption e rispondi in formato json con queste variabili:
- datetime: la data estratta dalla descrizione in questo formato 2023/mese/giornoTora_di_partenza:minuto_di_partenza:00Z
- nome_evento: il nome dell'evento estratto dalla descrizione
- artisti: nome degli artisti che suonano separato da una virgola
- luogo: luogo dell'evento
- costo: costo del biglietto, se possibile
"""

INSTAGRAM_IMAGE_ADDONS = """
- username: lo username dell'account instagram che ha postato l'evento, di solito dopo gli username di chi ha messo like al post e sempre prima della descrizione dell'evento
- link: https://instagram.com/[inserisci qui lo username del profilo instagram che ha postato evento]
"""

# I think we need to set default values for when stuff isnt found, just adding them to the prompt probably works
def create_prompt(description, username='', link='', source=''):
    prompt = ''
    if username != '' and link != '':
        prompt = PROMPT_CONTEXT + f"- username: {username}\n" + f"- link: {link}\n"
    else:
        prompt = PROMPT_CONTEXT
    prompt = prompt + f"Caption: '{description}'"    
    
    return prompt


def get_event_info(description, source, key, username='', link=''):
    openai.api_key = key
    prompt = create_prompt(description, username=username, link=link, source=source)
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].text.strip()