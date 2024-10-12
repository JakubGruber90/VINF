import sys
import re
import os
import time
import logging
import signal
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

###Constants and global variables
CURR_DIR = os.getcwd()
HTML_DATA_DIR = os.path.join(CURR_DIR, 'data', 'data_raw')
TEXT_DATA_DIR = os.path.join(CURR_DIR, 'data', 'data_text')
VISITED_LINKS_FILE = os.path.join(CURR_DIR, 'visited_links.pkl')
LAST_PAGE_FILE = os.path.join(CURR_DIR, 'last_page.pkl')

#Setup for logging
logging.basicConfig(filename='Crawler log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
LOGGER = logging.getLogger('|Crawler_SELENIUM_log|')

options = ChromeOptions() #Selenium setup
options.add_argument("--headless=old")
driver = webdriver.Chrome(options=options)

visited_links = set()
last_page = int
stop_crawler = False

###Function definitions
def crawl(start_url, page): #crawler logic
    global last_page
    page = int(page)
    global stop_crawler
    html_data = None
    text_data = None
    
    while not stop_crawler:
        url = start_url+f'page:{page}/'
        LOGGER.info(f'Crawling page {page} of Moby games game browser')
        
        try:
            driver.get(url)
            page_source = driver.page_source
            game_links = re.findall(r'<a\s+href="(\S+\/game\/\S+)">(?:.*?)<\/a>', page_source)
            
            for game in game_links:
                if game in visited_links: #if the link was already visited, just continue
                    LOGGER.info(f'Already visited link {game}')
                    continue                    
                else: #if it was not visited, save text and html data and save current as visited
                    driver.get(game)
                    html_data = driver.page_source
                    text_data = prepare_text_data(html_data)
                    visited_links.add(game)
                    save_files(html_data, text_data, game)
                    
                time.sleep(2) #sleep 2 seconds before visiting another link
        except Exception as e:
            save_visited_links()
            save_last_page()
            LOGGER.error(e)
        
        page += 1 #increment the page
        last_page = page
        time.sleep(2) 
        
def stop_crawling(sig, frame):
    LOGGER.info('Recieved SIGINT, stopping the crawler and saving visited links...')
    save_visited_links()
    save_last_page()
    global stop_crawler
    stop_crawler = True
    
def prepare_text_data(html_data): #function to extract only text from html files
    text_data = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script\s*>', '', html_data) #get rid of all script tags and their contents
    text_data = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style\s*>', '', text_data) #get rid os style tags and their contents
    text_data = re.sub(r'<[^>]+>', '', text_data) #get rid of other html tags
    
    return text_data
    
def save_files(html_data, text_data, url): #function to save raw html and text data from webpages
    game_name = game_name_from_url(url)
    raw_file = os.path.join(HTML_DATA_DIR, game_name+'.html')
    text_file = os.path.join(TEXT_DATA_DIR, game_name+'.txt')
    
    with open(raw_file, 'w', encoding='utf-8') as r:
        r.write(html_data)
    
    with open(text_file, 'w', encoding='utf-8') as t:
        t.write(text_data)
        
    LOGGER.info(f'Saved files from url: {url}', )
    
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

def load_last_page(): #Load last visited page number
    global last_page
    if os.path.exists(LAST_PAGE_FILE):
        with open(LAST_PAGE_FILE, 'rb') as f:
            last_page = pickle.load(f)
        LOGGER.info('Last page loaded successfully.')
    else:
        last_page = 1
        LOGGER.info('No previous last page remembered.')

def save_last_page():  # Save last page to a file
    with open(LAST_PAGE_FILE, 'wb') as f:
        pickle.dump(last_page, f)
        
    LOGGER.info('Last page successfully saved.')

###Main
if __name__ == '__main__':
    load_visited_links()
    load_last_page()   
    
    if len(sys.argv) > 1: 
        url = sys.argv[1] #url to start search from
    else:
         url = 'https://www.mobygames.com/game/sort:title/'
    
    if len(sys.argv) > 2 :
        page = sys.argv[2] #page to start from
    else:
        page = last_page
        
    signal.signal(signal.SIGINT, stop_crawling)
      
    crawl(url, page)