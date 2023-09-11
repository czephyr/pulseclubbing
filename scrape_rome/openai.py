import openai

PROMPT_CONTEXT = """
Sei una REST API, è il 2023. 
È importante che l'output sia un json valido, senza altre stringhe, che inizia con { e finisce con }.
Ci interessa raccogliere informazioni su eventi di Clubbing a Roma, di solito questi eventi sono descritti con una caption, esempio:

"Venerdì 14 luglio MERENDE presenta SUPERORGANISMO ❤️‍🔥
Dopo una intensa e calda stagione di Merende, apre il giardino di Nocturama e torna SUPERORGANISMO all'Angelo Mai.
Sound e live fuori, crazy tattoo session dentro e molto altro... ✨
Start: 19.00
Ingresso 6 euro + tessera Arci.
📧 prenotazioni@angelomai.org
LINE UP
@bunny__dakota
@la___diferencia
@555_inkindustriaindipendente"

Come esempio, questa è un corretto output:
{
    "date": "2023-07-14 19:00:00",
    "name": "Superorganismo",
    "artists": "Bunny Dakota, La Diferencia",
    "location": "Angelo Mai",
    "price": "6€ + tessera Arci",
    "organizer": "Angelo Mai",
    "link": "instagram.com/GasgGkj1981"
}

Questo invece è un output errato poiché contiene del testo che non è un json valido:
"Risposta:
{
    "date": "2023-09-15 19:00:00",
    "name": "Cabaret Astromusicale",
    "artists": "Astronza, DJ Leblond",
    "location": "Angelo Mai",
    "price": "Free",
    "organizer": "Angelo_Mai_Roma",
    "link": "instagram.com/p/CxDd9lWNKzn"
}"

Un esempio di caption che non è un evento di clubbing è:
'Citta sola. Un\'anteprima\ndi Olivia Laing\n\nper la regia di Alessandro Ferroni e Lisa Ferlazzo Natoli\nin scena all\' Angelo Mai dal 4 al 7 maggio\n\n"Immaginate di stare alla finestra, di notte, al sesto o al settimo o al quarantatreesimo piano di un edificio. La citta si rivela come un insieme di celle, centinaia di migliaia di finestre".\nOlivia Laing ragiona e cammina per le strade di New York disegnandone una mappa peculiare e affettiva, come una cartografia tracciata lungo l\'abisso dell\'isolamento. New York diventa grazie a Laing tutte le citta che abbiamo attraversato e racconta in maniera particolarissima una solitudine che puo essere solo urbana.\n\nLa compagnia teatrale lacasadargilla propone un\'opera per voce sola, dalla natura immersiva e installativa per restituire agli spettatori le formidabili pagine di Olivia Laing.\n\nIn scena all\'Angelo Mai il 4, 5, 6 maggio h 21.00 e il 7 maggio h 18.00\n\n@lacasadargilla\n\nInfo e prenotazioni prenotazioni@angelomai.org'

Principalmente questi eventi contengono informazioni riguardanti gli artisti che suonano, il luogo, il prezzo del biglietto e la data.
Se non trovi artisti, probabilmente non si tratta di un evento di clubbing, quindi devi rispondere con un json vuoto.

Raccogli le seguenti informazioni dalla caption e rispondi in formato json con queste variabili, devi rispondere solo in un formato json leggibile:
- date: la data estratta dalla descrizione in questo formato anno-mese-giorno ora_di_partenza:minuto_di_partenza:00 (se l'anno manca usa il corrente, è importante che la data sia in formato %Y-%m-%d %H:%M:%S)
- name: il nome dell'evento estratto dalla descrizione
- artists: nome degli artisti che suonano separato da una virgola
- location: luogo dell'evento
- price: costo del biglietto, se possibile, se non è possibile e il costo è gratuito, deve essere la stringa 'Free', ma solo se chiaramente esplicitato nella caption
"""

INSTAGRAM_IMAGE_ADDONS = """
- organizer: lo username dell'account instagram che ha postato l'evento, di solito dopo gli username di chi ha messo like al post e sempre prima della descrizione dell'evento
- link: https://instagram.com/[inserisci qui lo username del profilo instagram che ha postato evento]
"""

# I think we need to set default values for when stuff isnt found, just adding them to the prompt probably works
def create_prompt(description, username='', link='', source=''):
    prompt = ''
    if username != '' and link != '':
        # this means its an instagram link, so we already have those
        prompt = PROMPT_CONTEXT + f"- organizer: {username}\n" + f"- link: {link}\n"
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