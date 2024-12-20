import requests
from bs4 import BeautifulSoup

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


import aiohttp
import asyncio
from bs4 import BeautifulSoup

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


# urls = [
#     "https://www.gov.uk/register-for-self-assessment",
#     "https://www.gov.uk/register-for-vat"
# ]

# asyncio.run(parse_several_pages(urls))
