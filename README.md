# LLM-Based Linguistic Data Extractor

## Overview

A Python-based web scraper designed to generally extract linguistic data from websites using Large Language Models (LLMs). It takes in a base URL and sends its HTML content to an LLM (specifically via OpenRouter, but can be modified to inference locally). The LLM, using chain of thought reasoning, then interprets the structure of the page (pagination hierarchies, content structure) and sends back a structured JSON object with a) the content of the current page and b) the next page for traversal.

* main.py: Orchestrates the scraping process, manages concurrency, and handles data aggregation
* scrape.py: Fetches, normalizes HTML content
* inference.py: Helpers for LLM inference, including prompt generation and response parsing

## Functionality

1.  **Data Extraction:**
    * Dictionary Mode: When provided with source and target languages, it instructs the LLM to identify words, their translations, and example sentences, structuring them into a JSON dictionary
    * Raw Content Mode: When no target languages are specified, it instructs the LLM to extract all sentences from a page in the source language, structuring them as a JSON list of strings

2.  **Web Crawling, Pagination:**
    * The LLM is prompted to identify the "next page" URL in a sequence (e.g., pages of a dictionary or articles)
    * The scraper automatically enqueues and processes these subsequent pages

3.  **Concurrency:** Thread pool is utilized to process multiple web pages concurrently

4.  **Structured Output:** Saves extracted linguistic data into JSON files in the output/ directory (filenames reflect the languages involved or the source language for raw content)

## Usage

### Prerequisites

* Python 3.x
* requests library (pip install requests)
* openai library (pip install openai)
* OpenRouter API key (or compatible OpenAI API endpoint) configured in inference.py

### Running the Scraper

```bash
python main.py
