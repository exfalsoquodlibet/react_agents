from openai import OpenAI
import requests
import json
import asyncio
import os
from dotenv import load_dotenv

from openai_react_agents_from_scratch.utils import parse_several_pages

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Set up Google Search API key and engine ID
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def search_govuk(query, min_results=1):
    """
    Internet searches of the GOV.UK website for official UK government information return the formatted results.
    """
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={query}"
    response = requests.get(url)
    if response.status_code == 200:
        results = json.loads(response.text)
        if 'items' in results:
            # [{url: title}, ...]
            url_title_dicts = {results['items'][i]['link']: results['items'][i]['title'] for i in range(min(min_results, len(results['items'])))}
            # parse content for each URL
            url_content_dicts = asyncio.run(parse_several_pages(list(url_title_dicts.keys())))
            # combine url, title, and content into a list of dictionaries
            url_title_content_dicts = [{"url": url, "title": title, "content": url_content_dicts[url]} for url, title in url_title_dicts.items()]
            # print(f"URL title content dicts: {url_title_content_dicts}")
            results_list = [f"Title: {_dict['title']}\n Content: {_dict['content']}\n URL: {_dict['url']}" for _dict in url_title_content_dicts]
            # print(f"Results list: {results_list}")
            formatted_results = '\n\n'.join(results_list)

            # results_list = [
            #     f"Title: {results['items'][i]['title']}\nSnippet: {results['items'][i]['snippet']}\nURL: {results['items'][i]['link']}"
            #     for i in range(min(min_results, len(results['items'])))
            # ]
            # formatted_results = '\n\n'.join(results_list)
            # print(f"Formatted Google Search results: {formatted_results}")
            return formatted_results
        else:
            return "No results found."
    else:
        return f"Google Search error: {response.status_code}"
    
def ask_user(question):
    """
    Ask the user a question and return their response.
    """
    return input(f"Agent: {question}\nUser: ")

def get_llm_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        n=1,
        stop=None,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()
