import logging
import os
import arrow
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate

logger = logging.getLogger("mannaggia")

def instagram_event(description):
    template_string ="""You're tasked with extracting event information from the caption below delimited by triple backticks. The events you should focus on are clubbing events in Rome. If the event is related to theatre, cinema, film festival, or any non-musical event, YOU MUST return an empty JSON.
    caption: ```{caption}```
    {format_instructions}
    """

    response_schemas = [
        ResponseSchema(name="date", description=f"Date formatted as %Y-%m-%d %H:%M:%S, year is {arrow.now().year} if not found in the caption"),
        ResponseSchema(name="name", description="Name of the clubbing event"),
        ResponseSchema(name="artists", description="Names of performing artists, separated by commas (they could be written as instagram usernames, in case remove the @"),
        ResponseSchema(name="location", description="Venue of the event"),
        ResponseSchema(name="price", description="Ticket cost or 'Free' if explicitly mentioned")
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

    format_instructions = output_parser.get_format_instructions()
    prompt = PromptTemplate(
        template=template_string,
        input_variables=["caption"],
        partial_variables={"format_instructions": format_instructions}
    )

    llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo", openai_api_key=os.environ["OPENAI_API_KEY"])

    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(template_string)  
        ],
        input_variables=["caption"],
        partial_variables={"format_instructions": format_instructions},
        output_parser=output_parser
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    try:
        response = chain.predict_and_parse(caption=description)
        if response:
            logger.info(f"OpenAI response: {response}")
            if response['name'] == '':
                logger.info("Returned an empty name, no event returned")
                return None
            return response
    except Exception as xcp:
        logger.error(xcp)
        return None