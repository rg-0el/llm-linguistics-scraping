#!/usr/bin/env python3

import requests
import re
import json
from bs4 import BeautifulSoup

domain = "https://en.wiktionary.org"
start_page = "/wiki/Category:Adyghe_lemmas"
lg_name = "Adyghe"

def scrape_lemmas(start_url):
    url = domain + start_url
    page = 0
    lemmas = []

    while url:
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')

        page += 1
        print(f"Scraping page {page}")
        lines = soup.find('div', {'id': 'mw-pages'}).find_all('li')

        for line in lines:
            word = line.find('a').text.strip()
            if word:  # avoid empty entries
                lemmas.append(word)

        next_page_match = soup('a', text="next page")
        if next_page_match:
            next_page = next_page_match[0].attrs['href']
            url = domain + next_page
        else:
            url = None

    return lemmas

print("Starting lemma extraction...")
lemmas = scrape_lemmas(start_page)

print(f"Writing {len(lemmas)} lemmas to file...")
with open(f"{lg_name}_lemmas.txt", 'w', encoding='utf-8') as f:
    for lemma in lemmas:
        f.write(lemma + "\n")

print("Done.")
