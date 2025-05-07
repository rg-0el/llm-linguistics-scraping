import requests
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import html

import unicodedata

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

def normalize_url(raw):
    raw = html.unescape(raw.strip())
    p = urlparse(raw)

    # clean path, collapse '//' (keep trailing slash)
    path = "/".join(filter(None, p.path.split("/")))
    if p.path.endswith("/"):
        path += "/"
    path = "/" + path if not path.startswith("/") else path

    query = urlencode(sorted(parse_qsl(p.query, keep_blank_values=True)), doseq=True)
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, "", query, ""))

def scrape_url(url):
    response = requests.get(url, headers=HEADERS)
    text = unicodedata.normalize("NFKC", response.text)
    return text