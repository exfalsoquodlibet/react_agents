import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import aiohttp
import asyncio
import re


def get_and_parse_page_content(page_url):
    response = requests.get(page_url)
    if response.status_code == 200:

        soup = BeautifulSoup(response.text, 'html.parser')

        # extract the main content
        main_content = soup.find('main')

        # clean and print the text
        if main_content:
            return main_content.get_text(separator=' ', strip=True)
        else:
            print("Main content not found.")
            return ""
    else:
        print(f"Failed to fetch page, status code: {response.status_code}")
        return ""

# target_url = "https://www.gov.uk/register-for-self-assessment"
# get_and_parse_page_content(target_url)

async def fetch_and_parse(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        if response.status == 200:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')

            # Extract the main content
            main_content = soup.find('main')

            # Clean and return the text
            if main_content:
                return main_content.get_text(separator=' ', strip=True)
            else:
                print(f"Main content not found for {url}.")
                return ""
        else:
            print(f"Failed to fetch {url}, status code: {response.status}")
            return ""

async def parse_several_pages(urls: list[str]) -> list[dict[str, str]]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_parse(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # for url, content in zip(urls, results):
        #     print(f"\nContent from {url}:\n{content}\n")
        return dict(zip(urls, results))


def restructure_bankholiday_data(data: list[dict[str, str]]) -> list[dict[str, dict[str, str]]]:
    """
    Example input:
        [{"a": "2019-01-01"}, {"b": "2020-02-01"}, {"a": "2020-02-03"}, {"c": "2020-03-01"}]
    Example output:
        [{"2019": {"a": "2019-01-01"}}, {"2020": {"b": "2020-02-01", "a": "2020-02-03", "c": "2020-

    """
    result = defaultdict(dict)

    for item in data:
        for key, value in item.items():
            year = value.split("-")[0]
            result[year][key] = value
    
    return [{year: entries} for year, entries in result.items()]



def read_prompt_from_txt(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            prompt_content = file.read().strip()  
            return prompt_content
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return ""
    
def save_string_to_markdown(content: str, filename: str = "output.md"):
    """Saves a given string to a Markdown file."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Markdown file saved: {filename}")


def format_and_save_markdown(text: str, filename: str = "output.md"):
    """Formats structured text for better readability and saves it as a Markdown file."""

    # Define allowed headers and enforce consistent casing
    allowed_headers = ['Eureka Thought', 'Thought', 'Action', 'Action Input', 'Observation',  'Final Answer']

    # Format headers as bold (e.g., **Thought:**)
    for header in allowed_headers:
        text = re.sub(fr"\b{header}\s*:", fr"\n**{header}:**", text)

    # Ensure spacing before 'Eureka Thought' and 'Final Answer'
    text = re.sub(r"(\*\*Eureka Thought\*\:)", r"\n\n\1", text, flags=re.IGNORECASE)
    text = re.sub(r"(\*\*Thought\*\:)", r"\n\1", text, flags=re.IGNORECASE)
    text = re.sub(r"(\*\*Action\*\:)", r"\n\1", text, flags=re.IGNORECASE)
    text = re.sub(r"(\*\*Action Input\*\:)", r"\n\1", text, flags=re.IGNORECASE)
    text = re.sub(r"(\*\*Final Answer\*\:)", r"\n\n\1", text, flags=re.IGNORECASE)

    # Save to Markdown file
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)
    
    print(f"Formatted Markdown file saved: {filename}")