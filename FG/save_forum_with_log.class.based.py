import os
from bs4 import BeautifulSoup
import requests

# Base URL for the forums
base_url = "https://forum.flightgear.org/viewtopic.php?f={}&t={}"

# Directory to save the text file
download_dir = 'downloaded_forum_texts'
os.makedirs(download_dir, exist_ok=True)

# Log file to keep track of the last processed URL
log_file = os.path.join(download_dir, 'surveyed_forum_urls.txt')

# Set to keep track of visited URLs
visited_urls = set()

# Load the last processed state from the log file
last_f, last_t = 1, 1  # Default starting values
if os.path.exists(log_file):
    with open(log_file, 'r') as log:
        last_url = log.read().strip()
        if last_url.startswith("https://forum.flightgear.org/viewtopic.php?f="):
            _, params = last_url.split('?')
            param_dict = dict(param.split('=') for param in params.split('&'))
            last_f = int(param_dict['f'])
            last_t = int(param_dict['t']) + 1  # Start with the next `t`
            visited_urls.add(last_url)

# Function to extract only the main question and replies from 'content' class under 'postbody'
def extract_main_content(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')

    # Find all 'postbody' divs
    posts = soup.find_all('div', class_='postbody')

    extracted_texts = []
    for i, post in enumerate(posts):
        # Find 'content' divs within each 'postbody'
        content_divs = post.find_all('div', class_='content')
        for content_div in content_divs:
            # Extract text from each 'content' div and remove empty lines
            text_content = content_div.get_text(separator='\n').strip()
            lines = text_content.splitlines()
            # Filter out empty lines
            filtered_lines = [line for line in lines if line.strip()]
            # Determine if it's the question or a reply
            if filtered_lines:
                if i == 0:
                    extracted_texts.append(f"[Question]\n" + "\n".join(filtered_lines))
                else:
                    extracted_texts.append(f"[Reply]\n" + "\n".join(filtered_lines))

    return '\n'.join(extracted_texts)

# Function to process the forum pages
def download_forum_topics():
    global visited_urls  # Use the global variable `visited_urls`
    
    for f in range(last_f, 90):  # Resume from last_f to 89
        # Create a separate file for each `f`
        output_file = os.path.join(download_dir, f'forum_topics_f{f}.txt')
        consecutive_not_found = 0  # To track consecutive "not found" pages
        t = last_t if f == last_f else 1  # Start `t` from last_t for the first `f`
        
        with open(output_file, 'a', encoding='utf-8') as file:
            while consecutive_not_found < 2:  # Stop if we get 2 consecutive "not found"
                url = base_url.format(f, t)
                
                if url in visited_urls:
                    print(f'URL already visited: {url}')
                    t += 1
                    continue

                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        # Check for "The requested topic does not exist."
                        if "The requested topic does not exist." in response.text:
                            consecutive_not_found += 1
                            print(f'Topic not found at {url}, increasing counter to {consecutive_not_found}')
                            t += 1
                            continue
                        else:
                            consecutive_not_found = 0  # Reset counter on a valid page
                            
                            # Extract the main question and replies
                            main_content = extract_main_content(response.text)
                            
                            if main_content:  # Only save if there is content
                                # Write the URL and main content to the output file
                                file.write(f'URL: {url}\n{main_content}\n{"-"*80}\n')
                                print(f'Successfully downloaded and saved text from {url}')
                                
                                # Update the log file with the last processed URL
                                with open(log_file, 'w') as log:
                                    log.write(url + '\n')
                                    
                                visited_urls.add(url)
                    else:
                        print(f'Failed to access {url} with status code {response.status_code}')
                except Exception as e:
                    print(f'Error accessing {url}: {e}')
                
                # Increase t to check the next topic
                t += 1

# Start downloading and extracting forum topics
download_forum_topics()
