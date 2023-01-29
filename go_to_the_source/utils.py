import os
import json
import requests

import openai
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from go_to_the_source.constants import GOOGLE_API_KEY_ENV, GOOGLE_API_CX_ENV


def get_google_results(query: str) -> list:
    """returns a list of objects with 'title', 'link' and 'snippet' from
    the google search API after making the passed query"""
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


def prompt_gpt3(gpt_prompt: str) -> str:
    """returns the textual answer of GPT-3 (davinci 003) to the passed
    prompt"""
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


def web_page_to_text(url: str) -> str:
    """simply visit the passed url and convert it to human-readable text"""
    options = Options()
    options.add_argument("--no-sandbox")
    # not sure why yet, but I needed this
    options.add_argument("--remote-debugging-port=9222")

    options.binary_location = os.environ.get('CHROMIUM_LOCATION',
                                             '/usr/bin/chromium-browser')

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup.get_text()
