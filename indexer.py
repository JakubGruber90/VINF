import pickle
import os
import json
import re
from collections import defaultdict

def tokenize(json_obj: json):
    json_string = json.dumps(json_obj)
    json_string = re.sub(r'[^\w\s]', '', json_string).lower()
    tokens = json_string.split()
    
    return tokens

def serialize_doc_id(doc_id: dict):
    with open('doc_docID.pkl', 'wb') as p:
        pickle.dump(doc_id, p)

def serialize_term_id(term_id: dict):
    with open('term_termID.pkl', 'wb') as p:
        pickle.dump(term_id, p)

def serialize_index(index: dict):
    index_regular_dict = dict(index)
    with open('index.pkl', 'wb') as p:
        pickle.dump(index_regular_dict, p)

CURR_DIR = os.getcwd()
JSON_DATA_PATH = os.path.join(CURR_DIR, 'data', 'data_json')
JSON_DATA_DIR = os.fsencode(JSON_DATA_PATH)

index = defaultdict(lambda: (0, [])) #dictionary for index
term_id = {} #dictionary for termID - term couples
doc_id = {} #dictionary for docID - docName
next_term_id = 1 #variable for term IDs
next_doc_id = 1 #variable for doc IDs

if __name__ == '__main__':
    total_docs = 0
    
    for file in os.listdir(JSON_DATA_DIR):
        filename = os.fsdecode(file).split('.')[0]
        json_file = os.path.join(JSON_DATA_PATH, filename+'.json')
        total_docs += 1
        
        with open(json_file, 'r', encoding='utf-8') as f:
            open_file = json.load(f)
            
            doc_id[next_doc_id] = filename
            current_doc_id = next_doc_id
            next_doc_id +=1
            tokenized_doc = tokenize(open_file)
            term_doc_frequency = {} #dictionary for term - docFrequency
            
            for term in tokenized_doc:
                if term in term_doc_frequency:
                    term_doc_frequency[term] += 1
                else:
                    term_doc_frequency[term] = 1
            
                if term not in term_id:
                    term_id[term] = next_term_id
                    next_term_id += 1 
            
            for term, doc_frequency in term_doc_frequency.items():
                id_of_term = term_id.get(term)
                
                total_frequency, posting_list = index[id_of_term]
                total_frequency += doc_frequency
                posting_list.append((current_doc_id, doc_frequency, len(tokenized_doc)))
                index[id_of_term] = (total_frequency, posting_list)
                
    index['TOTAL_DOCS'] = total_docs
    serialize_doc_id(doc_id)
    serialize_term_id(term_id)
    serialize_index(index)