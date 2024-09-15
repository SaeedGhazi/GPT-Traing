import os
from bs4 import BeautifulSoup
import requests

# URLs to the category listings
category_pages = [
    'https://wiki.flightgear.org/w/index.php?title=Special:Categories&limit=500',
    'https://wiki.flightgear.org/w/index.php?title=Special:Categories&offset=FlightGear_Enhancement_Proposals&limit=500',
    'https://wiki.flightgear.org/w/index.php?title=Special:Categories&offset=Schleicher_ASK_21_screenhots&limit=500'
]

# Base URL format
base_url = "https://wiki.flightgear.org"

# Directory to save the downloaded HTML files
download_dir = 'downloaded_pages'
os.makedirs(download_dir, exist_ok=True)

# Log file to keep track of downloaded URLs
log_file = 'downloaded_urls.txt'

# Set to keep track of unique URLs
urls_to_download = set()
downloaded_urls = set()

# Load already downloaded URLs from the log file
if os.path.exists(log_file):
    with open(log_file, 'r') as log:
        downloaded_urls.update(line.strip() for line in log)

# Function to extract URLs from a webpage
def extract_urls_from_webpage(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find all 'a' tags with href attribute
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # Check if the link is an internal link and not already downloaded
                if href.startswith('/'):
                    full_url = base_url + href
                    if full_url not in downloaded_urls:
                        urls_to_download.add(full_url)
        else:
            print(f'Failed to access {url} with status code {response.status_code}')
    except Exception as e:
        print(f'Error accessing {url}: {e}')

# Extract initial URLs from the given category pages
for category_page in category_pages:
    extract_urls_from_webpage(category_page)

# Function to extract sublinks from a downloaded page
def extract_sublinks(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    sublinks = set()
    # Find all 'a' tags with href attribute
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Check if the link is an internal link and not already downloaded
        if href.startswith('/'):
            full_url = base_url + href
            if full_url not in downloaded_urls:
                sublinks.add(full_url)
    return sublinks

# Function to download URLs
def download_urls():
    with open(log_file, 'a') as log:
        while urls_to_download:
            url = urls_to_download.pop()
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    # Save the page content
                    # Use the URL path as filename, replacing '/' with '_'
                    page_path = url.replace(base_url, '').replace('/', '_')
                    file_name = os.path.join(download_dir, f'{page_path}.html')
                    
                    with open(file_name, 'w', encoding='utf-8') as file:
                        file.write(response.text)
                    
                    print(f'Successfully downloaded {url}')
                    # Log the downloaded URL
                    log.write(url + '\n')
                    downloaded_urls.add(url)
                    
                    # Extract sublinks and add to the set of URLs to download
                    sublinks = extract_sublinks(response.text)
                    urls_to_download.update(sublinks)
                else:
                    print(f'Failed to download {url} with status code {response.status_code}')
            except Exception as e:
                print(f'Error downloading {url}: {e}')

# Start downloading and extracting sublinks
download_urls()
