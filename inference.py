from openai import OpenAI
import json
import re

OPENROUTER_API_KEY = ""
MODEL = "meta-llama/llama-4-maverick" # can use oss, or write implementation for local inference
MAX_TRY_COUNT = 5

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)

# we tell the model to include a chain_of_thought for step-by-step reasoning, print it for debugging
def extract_chain_of_thought_from_response(response):
    match = re.search(r"<chain_of_thought>(.*?)</chain_of_thought>", response, re.DOTALL)
    return match.group(1) if match else None

# we tell the model to include a next_page for pagination
def extract_next_page_from_response(response):
    match = re.search(r'<next_page>(.*?)</next_page>', response, re.DOTALL)
    return match.group(1) if match else None

# we tell the model to wrap the response in a <json></json> tag so we can extract it in case it produces extra text
def extract_json_from_response(response):
    match = re.search(r'<json>(.*?)</json>', response, re.DOTALL)
    return match.group(1) if match else None

# for dictionary pages
def get_system_prompt_dictionary(language_to_translate, target_languages):
    prompt = f"""You will be provided with the HTML contents of a web page containing a dictionary of the language "{language_to_translate}", with target languages "{target_languages}".

You are responsible for carefully reading through and deconstructing the HTML, and determining its structure. Then, you will put together a JSON object that contains the dictionary contents of the page.

The JSON object should have the following structure:
```
{{
    "corpus": {{
        "word_in_language": {{
            "translations": {{
                "target_language_1": "definition of word_in_language in target_language_1",
                "target_language_n": "definition of word_in_language in target_language_n",
            }},
            "example_sentences": [{{
                "{language_to_translate}": "example sentence in {language_to_translate}",
                "target_language_1": "example sentence in target_language_1",
                "target_language_n": "example sentence in target_language_n",
                ...
            }}, ...]
        }},
        ...
    }}
}}
```

Ensure that ALL target languages are included in the JSON object. Also ensure that any and ALL examples sentences which contain the relevant word for a given entry are included in the appropriate example_sentences array. You are required to include ALL words and translations that are present on the page in the JSON object.

Constraints:
    Language
        - {language_to_translate}
    Target Language(s):
        - {target_languages}

Response instructions:
- Always include mappings for ALL indicated target languages, even if the word is not present in the dictionary (null)
- You are required to begin your response with a chain_of_thought tag, within which you will outline your thought process for determining the structure of the HTML and how you will go about parsing it. You will also detail in depth, thinking step-by-step through the structure and layout of the page/site, whether there is a logical next page to visit or not, and, if so, what the URL is. To do this, you are first REQUIRED to ENTIRELY verbalize and map out the HOLISTIC pagination structure of the entire website. Keep in mind that some websites have peculiar structures or multiple pagination hierarchies, and you should be lay out ALL of this. To ensure correctness, you are REQUIRED to list ALL of the possibilities you considered and why you chose the one you did. Be very careful when setting the next page to null, as the greater objective is to scrape the whole dictionary, A-Z, not just the current letter or word or page -- you are just working on a slice. Think logically.
- The next_page tag should be the full URL, not just the relative path, or null if you've determined there to be none.
- Your final JSON object MUST be wrapped in a <json></json> tag, and the whole response should be strictly structured like:
```
<response>
    <chain_of_thought>...</chain_of_thought>
    <next_page>...</next_page>
    <json>[json object here]</json>
</response>
```

IMPORTANT:
- You are NOT being asked to write code; you must manually extract, parse, and construct the JSON object yourself. Do not attempt to write code to generate the JSON object.
- You will potentially be dealing with an unfamiliar writing system, language, or character set. You must be able to handle and parse any and all characters that are present in the HTML, with HIGH FIDELITY (no loss of information, no corruption, no modification).
\n\n--------\n\n"""
    
    return prompt

# for raw content pages
def get_system_prompt_raw_content(language):
    prompt = f"""You will be provided with the HTML contents of a web page containing contents in the language "{language}".

You are responsible for carefully reading through and deconstructing the HTML, and determining its structure. Then, you will put together a JSON object that contains the contents of the page.

The JSON object should have the following structure:
```
{{
    "corpus": [
        "sentence1",
        "sentence2",
        ...
    ]
}}
```

Ensure that ALL sentences are included in the JSON object.

Constraints:
    Language
        - {language}

Response instructions:
- You are required to begin your response with a chain_of_thought tag, within which you will outline your thought process for determining the structure of the HTML and how you will go about parsing it. You will also detail in depth, thinking step-by-step through the structure and layout of the page/site, whether there is a logical next page to visit or not, and, if so, what the URL is. To do this, you are first REQUIRED to ENTIRELY verbalize and map out the HOLISTIC pagination structure of the entire website. Keep in mind that some websites have peculiar structures or multiple pagination hierarchies, and you should be lay out ALL of this. To ensure correctness, you are REQUIRED to list ALL of the possibilities you considered and why you chose the one you did. Be very careful when setting the next page to null, as the greater objective is to scrape the whole dictionary, A-Z, not just the current letter or word or page -- you are just working on a slice. Think logically.
- The next_page tag should be the full URL, not just the relative path, or null if you've determined there to be none.
- Your final JSON object MUST be wrapped in a <json></json> tag, and the whole response should be strictly structured like:
```
<response>
    <chain_of_thought>...</chain_of_thought>
    <next_page>...</next_page>
    <json>[json object here]</json>
</response>
```

IMPORTANT:
- You are NOT being asked to write code; you must manually extract, parse, and construct the JSON object yourself. Do not attempt to write code to generate the JSON object.
- You will potentially be dealing with an unfamiliar writing system, language, or character set. You must be able to handle and parse any and all characters that are present in the HTML, with HIGH FIDELITY (no loss of information, no corruption, no modification).
\n\n--------\n\n"""
    
    return prompt