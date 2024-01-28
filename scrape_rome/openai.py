import logging
import os
import json
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from datetime import datetime

logger = logging.getLogger("mannaggia")

def instagram_event(description, post_date: str):
    template_string =f'Today is {datetime.today().strftime("%A %d %B %Y")}.' + """You're tasked with extracting event information from the caption below delimited by triple backticks. The events you should focus on are clubbing events in Rome. If the event is related to theatre, cinema, film festival, or any non-musical event, YOU MUST return an empty JSON.
    This has been posted on Instagram on {post_date}:
    caption: ```{caption}```
    {format_instructions}
    """

    response_schemas = [
        ResponseSchema(name="date", description="Date formatted as %Y-%m-%d %H:%M:%S"),
        ResponseSchema(name="name", description="Name of the clubbing event"),
        ResponseSchema(name="artists", description="Names of performing artists, separated by commas (they could be written as instagram usernames, in case remove the @"),
        ResponseSchema(name="location", description="Venue of the event"),
        ResponseSchema(name="price", description="Ticket cost or 'Free' if explicitly mentioned")
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

    format_instructions = output_parser.get_format_instructions()
    prompt = PromptTemplate(
        template=template_string,
        input_variables=["caption", "post_date"],
        partial_variables={"format_instructions": format_instructions}
    )

    llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo", openai_api_key=os.environ["OPENAI_API_KEY"])
    
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(template_string)  
        ],
        input_variables=["caption", "post_date"],
        partial_variables={"format_instructions": format_instructions},
        output_parser=output_parser
    )
    chain = LLMChain(llm=llm, prompt=prompt, output_parser=output_parser)
    try:
        response = chain.run(caption=description, post_date=post_date)
        if response:
            logger.info(f"OpenAI response: {response}")
            if response['name'] == '':
                logger.info("Returned an empty name, no event returned")
                return None
            return response
    except json.decoder.JSONDecodeError:
        logger.error("JSON Error, possibly empty response.")
    except Exception as xcp:
        logger.error(xcp)
        return None