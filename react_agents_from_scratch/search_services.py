import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_govuk_services(query, page=1, top_n_results=5):
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


def search_govuk_services_string(query: str) -> str:
    """
    Format search results as a string
    
    Args:
        query (str): Search term
        
    Returns:
        str: Formatted search results
    """
    results = search_govuk_services(query)
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
