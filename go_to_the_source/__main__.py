import os
import requests
import json

import openai

"""
Let's make LLMs accountable! They are trapped in a cage without Internet
connection, but we can provide them with what they need to support their
claims. Given a claim, we are going to make them search Google until they
find a source that supports it!
"""


BASIC_CONTEXT = """I made the following question to an AI engine:

"{engine_question}"

The engine then told me:

"{engine_answer}"

I would like to verify this answer by searching Google and hopefully finding
a relevant page that likely contains information that confirms this.
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

GOOGLE_API_KEY_ENV = 'GOOGLE_API_KEY'
GOOGLE_API_CX_ENV = 'GOOGLE_API_CX'
OPENAI_KEY_ENV = 'OPENAI_KEY'

REQUIRED_ENV = [GOOGLE_API_KEY_ENV,
                GOOGLE_API_CX_ENV,
                OPENAI_KEY_ENV]


def get_google_results(query):
    # Make the request to the Google Search API
    url = 'https://customsearch.googleapis.com/customsearch/v1'
    params = {
        'q': query,
        'key': os.environ[GOOGLE_API_KEY_ENV],
        'cx': os.environ[GOOGLE_API_CX_ENV]
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        resp = json.loads(response.text)
        if 'items' not in resp:
            raise Exception(f'Google search {query} did not return anything!')
        return [
            {'title': i['title'],
             'link': i['link'],
             'snippet': i['snippet']}
            for i in resp['items']
        ]

    raise Exception(response.status_code)


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


def prompt_gpt3(gpt_prompt: str):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=gpt_prompt,
        temperature=0.7,
        max_tokens=256,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    return response['choices'][0]['text']


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

    for res in google_results:
        if res['title'] == suggested_title_result:
            print(f"\nGot it, must visit {res['link']} to confirm your claim!")
