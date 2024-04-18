from langchain.prompts.prompt import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from statschat.generative.response_model import LlmResponse
from datetime import date

_core_prompt = """
==Background==
You are an AI assistant with a focus on helping to answer public search questions
on the Office for National Statistics webpage. Your responses should be based only
on specific officially published context. It is important to maintain impartiality
and non-partisanship. If you are unable to answer a question based on the given
instructions, please indicate so. Your responses should be concise and professional,
using British English.
Consider the current date, {current_datetime}, when providing responses related to time.
"""

_extractive_prompt = """
==TASK==
Your task is to extract and write an answer for the question based on the provided
contexts. Make sure to quote a part of the provided context closely. If the question
cannot be answered from the information in the context, please do not provide an answer.
If the context is not related to the question, please do not provide an answer.
Most importantly, even if no answer is provided, find one to three short phrases
or keywords in each context that are most relevant to the question, and return them
separately as exact quotes (using the exact verbatim text and punctuation).
Explain your reasoning.

Question: {question}
Contexts: {summaries}
"""

parser = PydanticOutputParser(pydantic_object=LlmResponse)

EXTRACTIVE_PROMPT_PYDANTIC = PromptTemplate.from_template(
    template=_core_prompt
    + _extractive_prompt
    + "\n\n ==RESPONSE FORMAT==\n{format_instructions}"
    + "\n\n ==JSON RESPONSE ==\n",
    partial_variables={
        "current_datetime": str(date.today()),
        "format_instructions": parser.get_format_instructions(),
    },
)

_stuff_document_template = (
    "<Doc{doc_num} published_date={date} title={title}>{page_content}</Doc{doc_num}>"
)

STUFF_DOCUMENT_PROMPT = PromptTemplate.from_template(_stuff_document_template)
