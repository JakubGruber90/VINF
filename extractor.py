import re
import os
import json

CURR_DIR = os.getcwd()
TEXT_DATA_PATH = os.path.join(CURR_DIR, 'data', 'data_text')
HTML_DATA_PATH = os.path.join(CURR_DIR, 'data', 'data_raw')
JSON_DATA_PATH = os.path.join(CURR_DIR, 'data', 'data_json')
TEXT_DATA_DIR = os.fsencode(TEXT_DATA_PATH)

### Functions to extract key info with regex
def get_released(file):
    match = re.search(r'Released ((?:January|February|March|April|May|June|July|August|September|October|November|December)? ?[1-9]?[1-9]?,? ?\d{4})', file)
    return match.group(1) if match else 'N/A'

def get_publishers(file):
    match = re.search(r'Publishers(.*?)\s+(?=Developers|Moby Score)', file)
    return match.group(1).strip() if match else 'N/A'

def get_developers(file):
    match = re.search(r'Developers(.*?)\s+(?=Moby Score)', file)
    return match.group(1).strip() if match else 'N/A'

def get_moby_score(file):
    match = re.search(r'Moby Score ([0-9]\.[0-9])', file)
    return match.group(1) if match else 'N/A'

def get_critics_score(file):
    match = re.search(r'Critics (\d?\d%)', file)
    return match.group(1) if match else 'N/A'

def get_players_score(file): 
    match = re.search(r'Players(?:.*?)(\d\.\d stars)', file)
    return match.group(1) if match else 'N/A'

def get_genre(file):
    match = re.search(r'Genre (.*?)\s*(?=Perspective|Gameplay|Interface|Setting|Narrative|Misc)', file)
    
    if match:
        result = match.group(1).strip()
    else:
        return 'N/A'
    
    genre_exceptions = [
        'Racing / Driving',
        'Role-playing \(RPG\)',
        'Strategy / tactics'
    ]
    pattern = r'(' + '|'.join(genre_exceptions) + r'|[A-Z][a-z\-\s]*)'
    
    if result:
        genres = re.findall(pattern, result)
        return [genre.strip() for genre in genres]
    else:
        return 'N/A'   

def get_perspective(file):
    match = re.search(r'Perspective (.*?)\s*(?=Gameplay|Interface|Setting|Narrative|Misc|Business Model)', file)
    
    if match:
        result = match.group(1).strip()
    else:
        return 'N/A'
    
    pattern = r'([13A-Z].*?[a-z\-\s\/\']*)'
    
    if result:
        perspectives = re.findall(pattern, result)
        return [perspective.strip() for perspective in perspectives]
    else:
        return 'N/A' 

def get_gameplay(file):
    match = re.search(r'Gameplay (.*?)\s*(?=Interface|Setting|Narrative|Misc|Wanted)', file)
    
    if match:
        result = match.group(1).strip()
    else:
        return 'N/A'
    
    gameplay_exceptions = [
        'Japanese-style RPG \(JRPG\)',
        'Turn-based tactics \(TBT\)',
        'Quick Time Events \(QTEs\)',
        'Real-time strategy \(RTS\)',
        'Real-time tactics \(RTT\)',
        'Turn-based strategy \(TBS\)',
        'Turn-based tactics \(TBT\)',
        'Action RPG',
        'Tactical RPG',
        '4X',
        'Massively Multiplayer',
        'Paddle / Pong',
        'RPG elements'
    ]
    pattern = r'('+'|'.join(gameplay_exceptions)+r'|[4A-Z].*?[a-z\-\s\/\']*)'
    
    if result:
        gameplays = re.findall(pattern, result)
        return [gameplay.strip() for gameplay in gameplays]
    else:
        return 'N/A' 

def get_description(file):
    orig_desc_match = re.search(r'Official Description \(Ad Blurb\)(.*?)(?=Source)', file)
    desc_match = re.search(r'Description\n?(.*?)\n?(?=Spellings|Groups|Screenshots|Promos|Videos|Credits|Reviews|Critics|Trivia|Analytics|Related Games| Related sites|Identifiers|Contribute)', file)
   
    if orig_desc_match:
        return orig_desc_match.group(1).strip()
    elif desc_match:
        return desc_match.group(1).strip()
    else:
        return 'N/A'

### Main
if __name__ == '__main__': 
    for file in os.listdir(TEXT_DATA_DIR):
        filename = os.fsdecode(file).split('.')[0]
        
        print(f'Processing file {filename}\n') #DEBUG
        
        text_file_path = os.path.join(TEXT_DATA_PATH, filename+'.txt')
        html_file_path = os.path.join(HTML_DATA_PATH, filename+'.html')
        json_file = os.path.join(JSON_DATA_PATH, filename+'.json')
        
        with open(text_file_path, 'r', encoding='utf-8') as r:
            text_file = r.read()
        
        text_clean = ' '.join(text_file.split())  # Strip text file of unwanted whitespace characters for easier regex
        
        with open(html_file_path, 'r', encoding='utf-8') as r:
            html_file = r.read()
        
        data_dict = {
            'Released': get_released(text_clean),
            'Publishers': get_publishers(text_clean),
            'Developers': get_developers(text_clean),
            'Moby Score': get_moby_score(text_clean),
            'Critics Score': get_critics_score(text_clean),
            'Players Score': get_players_score(html_file),
            'Genre': get_genre(text_clean),
            'Perspective': get_perspective(text_clean),
            'Gameplay': get_gameplay(text_clean),
            'Description': get_description(text_clean)
        }
        
        with open(json_file, 'w') as j:
            json.dump(data_dict, j)
    
    print('DONE\n') #DEBUG