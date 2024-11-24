import pickle
import math
import re
import time

class bcolors:
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'

def load_doc_id():
    with open('doc_docID.pkl', 'rb') as p:
        return pickle.load(p)

def load_term_id():
    with open('term_termID.pkl', 'rb') as p:
        return pickle.load(p)

def load_index():
    with open('index.pkl', 'rb') as p:
        return pickle.load(p)

def tokenize_query(query: str):
    query = re.sub(r'[^\w\s]', '', query).lower()
    return query.split()

def parse_query(query: str):
    match = re.findall(r'\sor\s|\sOR\s', query)
    
    if ' ' in query and not match:
        terms = query.split(' ')
        operator = 'AND'
    elif match:
        terms = query.lower().split(' or ')
        operator = 'OR'
    else:
        terms = [query]
        operator = 'OR'
        
    return tokenize_query(' '.join(terms)), operator

###Modifications
def weighted_frequency(term_frequency: int):
    if term_frequency > 0:
        weighted_frequency = 1 + math.log10(term_frequency)
    elif term_frequency <= 0:
        weighted_frequency = 0
    
    return weighted_frequency

def max_term_freq(term_frequency: float, max_doc_frequency: int, alpha = 0.5):
    return alpha + ((1 - alpha) * (term_frequency / max_doc_frequency))

def probabilistic_idf(total_docs: int, docs_with_term: int):
    return max(0, math.log10((total_docs - docs_with_term) / (1 + docs_with_term)))

###Calculating scores
def calc_tf_idf_term(term_frequency: float, total_terms_in_document: int, total_docs: int, docs_with_term: int, max_doc_frequency: int,modifications: dict): #TF-IDF calculation with respect to modifications
    if modifications.get('weighted_freq'):
        tf = weighted_frequency(term_frequency)
    elif modifications.get('max_term_freq'):
        tf = max_term_freq(term_frequency, max_doc_frequency)
    else:
        tf = term_frequency / total_terms_in_document
    
    if modifications.get('probabilistic_idf'):
        idf = probabilistic_idf(total_docs, docs_with_term)
    else:
        idf = math.log((total_docs / (1 + docs_with_term)))
    
    return tf * idf

#calculating tf-idf score for the documents with respect to query and modifications
def calculate_scores(query_terms: list[str], term_id: dict, term_postings: dict, common_docs: set, total_docs: int, modifications: dict):
    doc_scores = {} #dictionary for docID - docScore
    for term in query_terms:
        if term in term_id:
            id_of_term = term_id[term]
            postings = term_postings[id_of_term]
            num_docs_with_term = len(postings)

            for (id_of_doc, term_frequency, total_terms_in_doc, max_doc_frequency) in postings:
                if id_of_doc in common_docs:
                    tf_idf_query_term = calc_tf_idf_term(term_frequency, total_terms_in_doc, total_docs, num_docs_with_term, max_doc_frequency, modifications)
                    
                    if id_of_doc not in doc_scores:
                        doc_scores[id_of_doc] = 0
                    doc_scores[id_of_doc] += tf_idf_query_term

    sorted_results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_results

###Search
def search(query: str, max_results: int, modifications: dict):
    doc_id = load_doc_id()
    term_id = load_term_id()
    index = load_index()
    total_docs = index['TOTAL_DOCS']

    query_terms, operator = parse_query(query)
    doc_sets = [] #list for sets of document IDs (documents containing query terms)
    term_postings = {} #dictionary for posting lists of terms

    for term in query_terms: #retrieving the posting lists for terms and ID of documents containing query terms
        if term in term_id:
            id_of_term = term_id[term]
            postings = index[id_of_term]
            term_postings[id_of_term] = postings
            doc_set = {id_of_doc for (id_of_doc, term_frequency, docs_with_term, max_doc_frequency) in postings}
            doc_sets.append(doc_set)

    if operator == 'AND': #keeping only doc IDs, that are either an intersection or union of query terms, according to operator
        common_docs = set.intersection(*doc_sets) if doc_sets else set()
    else:
        common_docs = set.union(*doc_sets) if doc_sets else set()

    sorted_results = calculate_scores(query_terms, term_id, term_postings, common_docs, total_docs, modifications)
    
    results = []
    for id_of_doc, score in sorted_results: #sorting results by score
        if len(results) < max_results:
            doc_name = doc_id[id_of_doc]
            results.append({
                'id_of_doc': id_of_doc,
                'doc_name': doc_name,
                'score': score
            })
        else:
            break

    return results

if __name__ == '__main__':
    modifications = {
        'weighted_freq': None,
        'max_term_freq': None,
        'probabilistic_idf': None
    }
    
    print(f'\n{bcolors.OKCYAN}What normalizations or modifications you want to use for calculating the score (write 0 or 1 separated by \',\' with no space to toggle off or on):{bcolors.ENDC}')
    print(f'{bcolors.OKCYAN}Weighted frequency(TF) | Max term frequency(TF) | Probabilistic IDF(IDF){bcolors.ENDC}')
    input_modifs = input().strip().split(',')
    int_modifs = [int(num) for num in input_modifs]
    
    for index,modif in enumerate(modifications):
        if int_modifs[index] == 0:
            modifications[modif] = False
        else:
            modifications[modif] = True
    
    end = False
    while not end:
        print('-----------------------------------------------------------------------------')
        print(f'\n{bcolors.OKCYAN}Enter your query. To end program, enter "END":{bcolors.ENDC}')
        user_input = input().strip()
        
        if user_input == 'END':
            end = True
            continue
        
        print(f'\n{bcolors.OKCYAN}Choose max number of results to display:{bcolors.ENDC}')
        max_results = int(input().strip())

        start_time = time.time()
        search_results = search(user_input, max_results, modifications)
        stop_time = time.time()
        
        if search_results:
            print(f'\n{bcolors.OKGREEN}Results:{bcolors.ENDC}')
            for result in search_results:
                print(f'DocID: {result["id_of_doc"]} || Document: {result["doc_name"]} || Score: {result["score"]}')
        else:
            print('No results')
        
        search_time = stop_time - start_time
        print(f'\n{bcolors.OKGREEN}Search time: {search_time} seconds{bcolors.ENDC}')
    
    print(f'\n{bcolors.WARNING}Ending program...{bcolors.ENDC}')
    time.sleep(1)