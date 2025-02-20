from openai import OpenAI
import requests
import json
import asyncio
import os
import urllib.parse
from bs4 import BeautifulSoup

from dotenv import load_dotenv

from react_agents_from_scratch.utils import parse_several_pages
from react_agents_from_scratch.utils import restructure_bankholiday_data

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Set up Google Search API key and engine ID
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def ask_user(question: str) -> str:
    """
    Ask the user a question and return their response.
    """
    return input(f"Agent: {question}\nUser: ")

def search_govuk(query: str, min_results: int=2) -> str:
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

            return formatted_results
        else:
            return "No results found."
    else:
        return f"Google Search error: {response.status_code}"

def get_llm_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "you are an AI assistant for the UK Government helping users navigate official government guidance and services."},
            {"role": "user", "content": prompt}
        ],
        n=1,
        stop=None,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()


def _search_govuk_services(query: str, page: int, top_n_results: int) -> list[dict[str, str]]:
    """
    Search GOV.UK services and return results
    
    Args:
        query (str): Search term
        page (int): Page number (default: 1)
        
    Returns:
        list: List of dictionaries containing service details
    """
    base_url = "https://www.gov.uk/search/services"
    
    # Construct the search URL with parameters
    params = {
        'keywords': query,
        'order': 'relevance',
        'page': page
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # find all service results
        results = []
        service_items = soup.find_all('li', class_='gem-c-document-list__item')
        
        for item in service_items[:top_n_results]:
            # extract title and link
            title_element = item.find('a', class_='govuk-link')
            title = title_element.text.strip() if title_element else "No title"
            link = f"https://www.gov.uk{title_element['href']}" if title_element else None
            
            # extract description
            description_element = item.find('p', class_='gem-c-document-list__item-description')
            description = description_element.text.strip() if description_element else "No description"
            
            # get sub-pages if they exist
            sub_pages = []
            sub_items = item.find_all('li', class_='gem-c-document-list-child')
            for sub_item in sub_items:
                sub_title_element = sub_item.find('a')
                sub_desc_element = sub_item.find('p')
                if sub_title_element and sub_desc_element:
                    sub_pages.append({
                        'title': sub_title_element.text.strip(),
                        'description': sub_desc_element.text.strip(),
                        'link': f"https://www.gov.uk{sub_title_element['href']}"
                    })
            
            results.append({
                'title': title,
                'description': description,
                'link': link,
                'sub_pages': sub_pages
            })
            
        return results
        
    except requests.RequestException as e:
        print(f"Error occurred: {e}")
        return []


def search_govuk_services(query: str, page=1, top_n_results=5) -> str:
    """
    Format search results as a string
    
    Args:
        query (str): Search term
        
    Returns:
        str: Formatted search results
    """
    results = _search_govuk_services(query=query, page=page, top_n_results=top_n_results)
    output = []
    
    output.append(f"Search results for '{query}':\n")
    
    for i, result in enumerate(results, 1):
        output.append(f"{i}. {result['title']}")
        output.append(f"   {result['description']}")
        output.append(f"   {result['link']}")
        
        if result['sub_pages']:
            output.append("\n   Sub-pages:")
            for sub_page in result['sub_pages']:
                output.append(f"   - {sub_page['title']}")
                output.append(f"     {sub_page['description']}")
                output.append(f"     {sub_page['link']}\n")
        output.append("")
    
    return "\n".join(output)

def _get_uk_bank_holidays():
    url = "https://www.gov.uk/bank-holidays.json"
    try:
        response = requests.get(url)
        response.raise_for_status()  # raise an error for HTTP issues
        bank_holidays = response.json()
        return bank_holidays
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bank holiday data: {e}")
        return None
    
def get_uk_bank_holidays_formatted():
    bank_holidays = _get_uk_bank_holidays()
    formatted_holidays = {}
    if bank_holidays:
        for region, _ in bank_holidays.items():
            formatted_holidays[region] = restructure_bankholiday_data([{holiday['title']: holiday['date']} for holiday in bank_holidays[region]['events']])
        return formatted_holidays
    else:
        return "No bank holiday data available."
