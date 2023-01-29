import os
import sys
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


BASIC_CONTEXT = """I made the following question to an AI engine:

"{engine_question}"

The engine then told me:

"{engine_answer}"

I would like to verify this answer by searching Google and hopefully finding
a relevant page that contains information that confirms this.
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
So we have found the following web page content that must confirm this answer.
Here is the web page content, verbatim, enclosed between START_OF_PAGE and
END_OF_PAGE:

-------------
START_OF_PAGE
{crawled_page}
END_OF_PAGE
-------------

After reading this content, would you say the answer "{engine_question}" 
to the question "{engine_answer}" has been confirmed or contradicted?
Please answer one of the three options: 
"Yes, confirmed", "Neither confirmed nor contradicted" or 
"Contradicted, I now think the right answer is: ..."
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

    gpt_select_result_prompt = get_prompt_for_google_result(
        engine_question=engine_question,
        engine_answer=engine_answer,
        google_search_query=suggested_search_query,
        search_results=google_results)

    print(f"\nWe ask GPT-3: {gpt_select_result_prompt}")

    gpt_answer = prompt_gpt3(gpt_prompt=gpt_select_result_prompt)

    print(f"GPT-3 answers: {gpt_answer}")

    suggested_title_result = gpt_answer.strip().replace('"', '')

    reference_link = None

    for res in google_results:
        # sometimes GPT removes punctuations
        if suggested_title_result in res['title']:
            print(f"\nGot it, must visit {res['link']} to confirm your claim!")
            reference_link = res['link']

    if not reference_link:
        print('GPT-3 found no relevant page in Google search results to '
              'confirm its claim!')
        sys.exit(1)

    print('Attempting to crawl the selected link...')
    crawled_page = web_page_to_text(reference_link)

    # reasonably trim the crawled content to avoid exceeding the prompt length
    crawled_page = crawled_page[:min(len(crawled_page),
                                     MAX_PROMPT_LENGTH - 1000)]

    gpt_confirmation_prompt = get_prompt_for_confirmation(
        engine_question=engine_question,
        engine_answer=engine_answer,
        crawled_page=crawled_page)

    print(f"\nWe ask GPT-3: {gpt_confirmation_prompt}")

    gpt_answer = prompt_gpt3(gpt_prompt=gpt_confirmation_prompt)

    print(f"GPT-3 answers: {gpt_answer}")
