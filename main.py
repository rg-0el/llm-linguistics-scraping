from pathlib import Path

import json
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

from scrape import scrape_url, normalize_url
from inference import (
    client,
    MODEL,
    get_system_prompt_dictionary,
    get_system_prompt_raw_content,
    extract_json_from_response,
    extract_chain_of_thought_from_response,
    extract_next_page_from_response,
)
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

# config
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_WORKERS = 20
MAX_LLM_ATTEMPTS = 3

# globals, locks
DICT_LOCK = threading.Lock()  # protect master dict
VISIT_LOCK = threading.Lock()  # protect visited_urls, enqueue
FILE_LOCK = threading.Lock()  # protect disk file writes

visited_urls = set()
dictionary = None

executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
futures = set()  # live futures pool
futures_lock = threading.Lock()  # guards futures set

# helpers
def save_json(data, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=4)

def save_json_threadsafe(snapshot, path):
    with FILE_LOCK:
        save_json(snapshot, path)

def track(fut):
    # remove finished future from pool
    with futures_lock:
        futures.discard(fut)

def enqueue_new(url, source_language, target_languages, out_path):
    url = normalize_url(url)
    if not url:
        return False

    with VISIT_LOCK:
        if url in visited_urls:
            return False
        visited_urls.add(url)

    # schedule page
    future = executor.submit(process_page, url, source_language, target_languages, out_path)
    future.add_done_callback(track)
    with futures_lock:
        futures.add(future)
    return True

# worker
def process_page(url, source_language, target_languages, out_path):
    # scrape single URL, stream LLM, cascade <next_page>, retry on failures
    for attempt in range(1, MAX_LLM_ATTEMPTS + 1):
        try:
            print(f"Scraping {url} (attempt {attempt}/{MAX_LLM_ATTEMPTS})")
            # download raw HTML
            html = scrape_url(url)

            # determine which prompt to use
            if target_languages:
                system_prompt_content = get_system_prompt_dictionary(source_language, target_languages)
            else:
                system_prompt_content = get_system_prompt_raw_content(source_language)

            # streaming llm call
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": system_prompt_content
                        + html
                        + "\n\nBegin. ",
                    }
                ],
                temperature=0.1,
                stream=True,
            )

            buf, dispatched = [], False
            for event in completion:
                chunk = event.choices[0].delta.content or ""
                buf.append(chunk)

                # first time we see </next_page> -> enqueue successor
                if not dispatched:
                    next_page = extract_next_page_from_response("".join(buf))
                    if next_page:
                        if enqueue_new(next_page, source_language, target_languages, out_path):
                            dispatched = True

            # parse json
            full_resp = "".join(buf)
            chain_of_thought = extract_chain_of_thought_from_response(full_resp)
            print("Chain of thought for " + url + ": " + (chain_of_thought or "empty"))
            page_dict = json.loads(extract_json_from_response(full_resp))
            break  # success -> exit retry-loop

        except Exception as exception:
            print(f"Attempt {attempt} failed for {url}: {exception}")
            if attempt == MAX_LLM_ATTEMPTS:
                print(f"Giving up {url} after {MAX_LLM_ATTEMPTS} attempts")
                page_dict = {}
            else:
                continue

    # merge new dictionary into master
    with DICT_LOCK:
        corpus_from_llm = page_dict.get("corpus")
        num_added = 0

        if corpus_from_llm is not None:
            if isinstance(dictionary, list) and isinstance(corpus_from_llm, list):
                # if corpus_from_llm is a list, extend dictionary with it
                dictionary.extend(corpus_from_llm)
                num_added = len(corpus_from_llm)
            elif isinstance(dictionary, dict) and isinstance(corpus_from_llm, dict):
                # if corpus_from_llm is a dict, update dictionary with it
                dictionary.update(corpus_from_llm)
                num_added = len(corpus_from_llm)

            if isinstance(dictionary, list):
                temp = list(dictionary) # shallow copy of list
            elif isinstance(dictionary, dict):
                temp = dict(dictionary) # shallow copy of dict
            else: # on error, just use the dictionary as is
                temp = dictionary

            save_json_threadsafe(temp, out_path)
            print(f"Finished {url} (+{num_added} entries)")
        else:
            print(f"Finished {url} (no corpus data to add)")

def main():
    global dictionary

    start_url = input("URL: ").strip()
    source_language = input("Language to translate: ").strip()

    target_languages_input = input("Target languages (leave none for raw content scrape): ").strip()
    target_languages = target_languages_input if len(target_languages_input) > 0 else None

    if target_languages is None:
        out_path = str(OUTPUT_DIR / f"corpus_{source_language}.json")
        dictionary = [] # list for raw content (list of sentences)
        print(f"Starting raw content scrape, writing to {out_path}")
    else:
        out_path = str(OUTPUT_DIR / f"{source_language}_to_{target_languages}.json")
        dictionary = {} # dict for dictionary entries
        print(f"Starting dictionary crawl, writing to {out_path}")
    
    print(f"Starting crawl, writing to {out_path}")

    enqueue_new(start_url, source_language, target_languages, out_path)

    # wait for futures pool to empty
    while True:
        with futures_lock:
            if not futures:
                break
            current = set(futures)
        wait(current, return_when=FIRST_COMPLETED)
        time.sleep(0.1)

    executor.shutdown(wait=True)
    print(f"\nTotal entries collected: {len(dictionary)}")

if __name__ == "__main__":
    main()
