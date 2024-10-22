import pickle
import math
import re
import time

def load_doc_id():
    with open('doc_docID.pkl', 'rb') as p:
        return pickle.load(p)

def load_term_id():
    with open('term_termID.pkl', 'rb') as p:
        return pickle.load(p)

def load_index():
    with open('index.pkl', 'rb') as p:
        return pickle.load(p)

def tokenize_query(query):
    query = re.sub(r'[^\w\s]', '', query).lower()
    return query.split()

def parse_query(query):
    if 'AND' in query:
        terms = query.split(' AND ')
        operator = 'AND'
    elif 'OR' in query:
        terms = query.split(' OR ')
        operator = 'OR'
    else:
        terms = [query]
        operator = 'OR'
    return tokenize_query(' '.join(terms)), operator

def calculate_tf_idf(term_frequency, total_terms_in_document, total_docs, docs_with_term):
    tf = term_frequency / total_terms_in_document
    idf = math.log(total_docs / docs_with_term)
    return tf * idf

def search(query, max_results):
    doc_id = load_doc_id()
    term_id = load_term_id()
    index = load_index()
    total_docs = index['TOTAL_DOCS']

    query_terms, operator = parse_query(query)
    doc_sets = []
    term_postings = {}

    for term in query_terms:
        if term in term_id:
            id_of_term = term_id[term]
            total_term_frequency, postings = index[id_of_term]
            term_postings[id_of_term] = postings
            doc_set = {id_of_doc for (id_of_doc, _, _) in postings}
            doc_sets.append(doc_set)

    if operator == 'AND':
        common_docs = set.intersection(*doc_sets) if doc_sets else set()
    else:
        common_docs = set.union(*doc_sets) if doc_sets else set()

    doc_scores = {}
    for term in query_terms:
        if term in term_id:
            id_of_term = term_id[term]
            postings = term_postings[id_of_term]
            num_docs_with_term = len(postings)

            for (id_of_doc, term_frequency, total_terms_in_doc) in postings:
                if id_of_doc in common_docs:
                    tf_idf = calculate_tf_idf(term_frequency, total_terms_in_doc, total_docs, num_docs_with_term)
                    if id_of_doc not in doc_scores:
                        doc_scores[id_of_doc] = 0
                    doc_scores[id_of_doc] += tf_idf

    sorted_results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for id_of_doc, score in sorted_results:
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
    end = False
    while not end:
        print('\nEnter your query (use operators AND, OR between seearched words). To end program, enter "END":')
        user_input = input().strip()
        if user_input == 'END':
            end = True
            continue
        
        print('Choose number of results to be shown:')
        max_results_str = input().strip()
        max_results = int(max_results_str)
        
        search_results = search(user_input, max_results)
        if search_results:
            for result in search_results:
                print(f'DocID: {result["id_of_doc"]}, Document: {result["doc_name"]}, Score: {result["score"]}')
        else:
            print('No results')
    
    print('\nEnding program...')
    time.sleep(2)