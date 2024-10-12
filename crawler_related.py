import sys
import re
import os
import time
import logging
import signal
import pickle
import urllib3

###Constants and global variables
CURR_DIR = os.getcwd()
HTML_DATA_DIR = os.path.join(CURR_DIR, 'data', 'data_raw')
TEXT_DATA_DIR = os.path.join(CURR_DIR, 'data', 'data_text')
VISITED_LINKS_FILE = os.path.join(CURR_DIR, 'visited_links.pkl')
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'accept-language': 'en',
    'from': 'jakubgruber90@gmail.com'
}

#Setup for logging
logging.basicConfig(filename='Crawler_RELATED_log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
LOGGER = logging.getLogger('|Crawler_RELATED_log|')

visited_links = set()
stop_crawler = False
http = urllib3.PoolManager()
logging.getLogger("urllib3").setLevel(logging.WARNING)

###Function definitions
def crawl(start_url): #crawler logic
    global stop_crawler
    html_data = None
    text_data = None
    to_visit = [start_url]
    
    while not stop_crawler:
        try:
            if to_visit:
                for page in to_visit:
                    if stop_crawler: 
                        break
                    
                    LOGGER.info(f'Crawling {page}')
                    
                    current_page = to_visit.pop(0)
                        
                    if current_page not in visited_links:
                        html_data = http.request('GET', current_page, headers=HEADERS).data
                        text_data = prepare_text_data(html_data)
                        save_files(html_data, text_data, current_page)
                        new_links = find_related_games(html_data)
                        non_visited_links = check_for_visited_games(new_links)
                        to_visit.extend(non_visited_links)
                        visited_links.add(current_page)
                    else:
                        LOGGER.info(f'Already visited link {current_page}')
                        continue               
                        
                    time.sleep(1)
            else:
                LOGGER.info('No more links left to visit')
                save_visited_links()
                stop_crawler = True      
        except Exception as e:
            save_visited_links()
            LOGGER.error(e)
        
def stop_crawling(sig, frame): #function to stop the crawler
    LOGGER.info('Recieved SIGINT, stopping the crawler and saving visited links...')
    save_visited_links()
    global stop_crawler
    stop_crawler = True

def check_for_visited_games(links): #function to remove links, that have already been visited
    non_visited_links = [link for link in links if link not in visited_links]
    return non_visited_links

def find_related_games(html_data): #function to extract all links to games in the related gaes section
    html_data = html_data.decode('utf-8')
        
    related_section = re.search(r'<section id="relatedGames">([\s\S]*?)</section>', html_data)
    
    if related_section:
        related_section_links = related_section.group(1)
        game_links_list = re.findall(r'<a\s+href="([^"]+)"', related_section_links)
        game_links_list = list(dict.fromkeys(game_links_list)) #removing duplicate links (from pictures and text anchors)
    
    return game_links_list
    
def prepare_text_data(html_data): #function to extract only text from html files
    html_data = html_data.decode('utf-8')
    text_data = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script\s*>', ' ', html_data) #get rid of all script tags and their contents
    text_data = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style\s*>', ' ', text_data) #get rid os style tags and their contents
    text_data = re.sub(r'<[^>]+>', '', text_data) #get rid of other html tags
    
    return text_data
    
def save_files(html_data, text_data, url): #function to save raw html and text data from webpages
    html_data = html_data.decode('utf-8')
    game_name = game_name_from_url(url)
    raw_file = os.path.join(HTML_DATA_DIR, game_name+'.html')
    text_file = os.path.join(TEXT_DATA_DIR, game_name+'.txt')
    
    with open(raw_file, 'w', encoding='utf-8') as r:
        r.write(html_data)
    
    with open(text_file, 'w', encoding='utf-8') as t:
        t.write(text_data)
        
    LOGGER.info(f'Saved files from url: {url}')
    
def game_name_from_url(url: str): #function to extract the game name from the url
    return url.split('/')[-2]

def save_visited_links():  # Save visited links to a file
    with open(VISITED_LINKS_FILE, 'wb') as f:
        pickle.dump(visited_links, f)
        
    LOGGER.info('Visited links successfully saved.')

def load_visited_links():  # Load visited links from a file
    global visited_links
    if os.path.exists(VISITED_LINKS_FILE):
        with open(VISITED_LINKS_FILE, 'rb') as f:
            visited_links = pickle.load(f)
        LOGGER.info('Visited links loaded successfully.')
    else:
        LOGGER.info('No previous visited links found.') 

###Main
if __name__ == '__main__': # https://www.mobygames.com/game/77086/the-talos-principle-prototype-dlc/ CONTINUE HERE
    load_visited_links()
    signal.signal(signal.SIGINT, stop_crawling)
    
    if len(sys.argv) > 1: 
        url = sys.argv[1] #url to start search from
        crawl(url)
    else:
        print('No url to start crawl from provided')