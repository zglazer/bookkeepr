import requests
from .. import app

def query(query_string):
    params = {'q': query_string, 'key': app.config['GOOGLE_API_KEY'], 'prettyPrint': 'false', 'printType': 'books'}
    r = requests.get(app.config['GOOGLE_BOOKS_API_URI ']+ 'volumes', params = params)
    if r.status_code != 200:
        return None
    return r.json()

def query_by_id(volume_id):
    r = requests.get(app.config['GOOGLE_BOOKS_API_URI'] + 'volumes/' + volume_id)
    if r.status_code != 200:
        return None
    return r.json()

def query_paginate(query_string, _index):
    params = {'q': query_string, 'key': app.config['GOOGLE_API_KEY'], 'prettyPrint': 'false', 'printType': 'books',
                'startIndex': _index}
    r = requests.get(app.config['GOOGLE_BOOKS_API_URI'] + 'volumes', params = params)
    if r.status_code != 200:
        return None
    return r.json()

class SearchHandler():
    _instance = None
    _index = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def query(self, query_string):
        params = {'q': query_string, 'key': app.config['GOOGLE_API_KEY'], 'prettyPrint': 'false', 'printType': 'books',
                    'startIndex': _index}
        r = requests.get(app.config['GOOGLE_BOOKS_API_URI'] + 'volumes', params = params)
        if r.status_code != 200:
            return None
        _index += MAX_RESULTS
        return r.json()

    def paginate(self, startIndex):
        params = {'q': query_string, 'key': app.config['GOOGLE_API_KEY'], 'prettyPrint': 'false', 'printType': 'books',
                    'startIndex': _index}
        r = requests.get(app.config['GOOGLE_BOOKS_API_URI'] + 'volumes', params = params)
        if r.status_code != 200:
            return None
        _index += MAX_RESULTS
        return r.json()



        