import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Base URL to start with
base_url = "https://gambaswiki.org/wiki/"

# Set to store visited URLs to avoid duplicates
visited_urls = set()

# Function to fetch and parse a page
def fetch_page(url):
    try:
        print(f"Fetching: {url}")  # Log the URL being fetched
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None

# Recursive function to explore links within the wiki folder
def explore_and_collect(url, depth=0, max_depth=2):
    if depth > max_depth or url in visited_urls:
        return ""
    
    visited_urls.add(url)
    
    # Fetch and parse the page
    soup = fetch_page(url)
    if soup is None:
        return ""
    
    print(f"Collected content from: {url}")  # Log after successfully collecting content
    
    # Collect content of the current page
    page_content = str(soup)
    
    # Find all links that are within the wiki folder
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        full_link = urljoin(base_url, link)
        
        # Only follow links under the /wiki/ path
        if full_link.startswith(base_url) and '/wiki/' in full_link:
            page_content += explore_and_collect(full_link, depth + 1, max_depth)
    
    return page_content

# Start collecting content from the base page
print("Starting collection from base URL...")
collected_content = explore_and_collect(base_url)

# Save all content to a single HTML file
output_file = "combined_wiki.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(collected_content)

print(f"Combined content saved to {output_file}")
