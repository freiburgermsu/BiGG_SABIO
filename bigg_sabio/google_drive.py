# -*- coding: utf-8 -*-
"""
Created on Thu Feb  3 00:15:06 2022

@author: Andrew Freiburger
"""

import requests
​
def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"
​
    session = requests.Session()
​
    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = get_confirm_token(response)
​
    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)
​
    save_response_content(response, destination)    
​
def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
​
    return None
​
def save_response_content(response, destination):
    CHUNK_SIZE = 32768
​
    f = open(destination, "wb")
    for chunk in response.iter_content(CHUNK_SIZE):
        if chunk: # filter out keep-alive new chunks
            f.write(chunk)
    f.close()
​
if __name__ == "__main__":
    file_id = r'1jCnx9OBiwYcKY5sN7mPJfcOQEXi-EXoF'
    destination = r'C:\Users\Ethan\Documents\Python\SABIO\test-2.txt'
    download_file_from_google_drive(file_id, destination)