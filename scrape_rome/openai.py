import openai

PROMTP_CONTEXT = """
È il 2023, il messaggio che segue delimitato dalle virgolette è la caption di un post instagram descrivente un evento.
Raccogli le seguenti informazioni dalla descrizione e rispondi in formato json con queste variabili:
- datetime: la data estratta dalla descriozione in questo formato 2023/mese/giornoTora_di_partenza:minuto_di_partenza:00Z
- nome_evento: il nome dell'evento estratto dalla descrizione
- artisti: nome degli artisti che suonano separato da una virgola
- luogo: luogo dell'evento
- costo: costo del biglietto, se possibile
"""

def get_event_info(description, openai_key):
    openai.api_key = openai_key

    prompt = PROMTP_CONTEXT + f'"{description}"'

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