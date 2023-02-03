import os
import json

import openai

from go_to_the_source.constants import REQUIRED_ENV, OPENAI_KEY_ENV,\
    MAX_PROMPT_LENGTH
from go_to_the_source.utils import prompt_gpt3, get_google_results,\
    web_page_to_text

"""
Let's make LLMs accountable! They are trapped in a cage without Internet
connection, but we can provide them with what they need to support their own
claims. Given a claim, we are going to make them search Google until they
find a source that supports it! Because we are whole-hearted, we are then also
going to give them the chance to either confirm or dismiss what they said,
and instead provide a different answer.
"""


BASIC_CONTEXT = """I made you the following question:

"{engine_question}"

You then answered:

"{engine_answer}"

AI engines are sometimes wrong. Therefore I would like to either verify or 
disclaim this answer by searching in Google and finding a page with content 
relevant to this question and answer.
"""

PROMPT_FOR_GOOGLE_SEARCH_TEMPLATE = """{prompt_context}
What would be a good search query that I could use to do that? Please write
the text that should be used to search Google, and nothing more. 
"""

PROMPT_FOR_GOOGLE_RESULT = """{prompt_context}
So I have searched Google for "{google_search_query}" and got the following
results in JSON format from its search API:

{google_results_json}

Which of these would you consider the most relevant source that I should 
click on? Please write the title of the result I should click on, and nothing
else. If no result is relevant enough from this list, please answer "None". 
"""

PROMPT_FOR_CONFIRMATION = """{prompt_context}
After searching, we have found the following web page content that either 
confirms or disclaims the answer to the question.
Here is the web page content, verbatim, enclosed between START_OF_PAGE and
END_OF_PAGE. Please pay close attention to it, especially if you find
 sentences that clearly disclaim the answer to the question given!

-------------
START_OF_PAGE
{crawled_page}
END_OF_PAGE
-------------

After reading this content, would you now say the answer "{engine_answer}" 
to the question "{engine_question}" has been confirmed or disclaimed?
Please answer one of the three options: 
1 - "Yes, confirmed as mentioned in: ..." (please quote supporting text from the web page content)
2 - "Neither confirmed nor disclaimed"
3 - "Disclaimed, I now think the right answer is: ..."
"""


def get_basic_context(engine_question: str, engine_answer: str):
    return BASIC_CONTEXT.format(engine_question=engine_question,
                                engine_answer=engine_answer)


def get_prompt_for_google_search(engine_question: str, engine_answer: str):
    return PROMPT_FOR_GOOGLE_SEARCH_TEMPLATE.format(
        prompt_context=get_basic_context(engine_question,
                                         engine_answer))


def get_prompt_for_google_result(engine_question: str, engine_answer: str,
                                 google_search_query: str,
                                 search_results: dict):
    return PROMPT_FOR_GOOGLE_RESULT.format(
        prompt_context=get_basic_context(engine_question,
                                         engine_answer),
        google_search_query=google_search_query,
        google_results_json=json.dumps(search_results, indent=4))


def get_prompt_for_confirmation(engine_question: str, engine_answer: str,
                                crawled_page: str):
    return PROMPT_FOR_CONFIRMATION.format(
        prompt_context=get_basic_context(engine_question,
                                         engine_answer),
        crawled_page=crawled_page,
        engine_question=engine_question,
        engine_answer=engine_answer)


if __name__ == '__main__':
    if not all([env_key in os.environ for env_key in REQUIRED_ENV]):
        raise ValueError(f'Required environment variables: {REQUIRED_ENV}')

    openai.api_key = os.environ[OPENAI_KEY_ENV]

    engine_question = input(
        'Please input a simple (single-line) prompt '
        'that you want to make to GPT-3: ')
    engine_answer = prompt_gpt3(engine_question).strip()

    print(f"GPT-3 says: {engine_answer}")
    print("Now let's make GPT-3 accountable!")

    gpt_search_prompt = get_prompt_for_google_search(
        engine_question=engine_question,
        engine_answer=engine_answer)

    print(f"\nWe ask GPT-3: {gpt_search_prompt}")

    gpt_answer = prompt_gpt3(gpt_prompt=gpt_search_prompt)
    suggested_search_query = gpt_answer.strip().replace('"', '')

    print(f"GPT-3 answers: {gpt_answer}")

    google_results = get_google_results(suggested_search_query)

    for res in google_results:
        print(f"Attempting to crawl {res['link']}")
        crawled_page = web_page_to_text(res['link'])

        # reasonably trim the crawled content to avoid exceeding the prompt
        # length
        crawled_page = crawled_page[:min(len(crawled_page),
                                         MAX_PROMPT_LENGTH - 1000)]

        gpt_confirmation_prompt = get_prompt_for_confirmation(
            engine_question=engine_question,
            engine_answer=engine_answer,
            crawled_page=crawled_page)

        print(f"\nWe ask GPT-3: {gpt_confirmation_prompt}")

        gpt_answer = prompt_gpt3(gpt_prompt=gpt_confirmation_prompt)

        print(f"GPT-3 answers: {gpt_answer}")

        if 'neither' not in gpt_answer.lower():
            break
