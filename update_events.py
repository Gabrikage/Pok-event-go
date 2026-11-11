"""Estrae titoli e collegamenti dal sito ufficiale Pokémon GO.
Non inventa date degli eventi: published è la data della notizia, se disponibile.
"""
import datetime as dt
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

BASE = 'https://pokemongolive.com'
PAGES = [BASE + '/news', BASE + '/en/news']
OUT = Path(__file__).with_name('events.json')
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; PokeEventGO/1.0; personal-news-aggregator)'}

def category(title):
    t = title.casefold()
    if 'community day' in t: return 'Community Day'
    if any(x in t for x in ('raid', 'raid hour', 'raid day')): return 'Raid'
    if any(x in t for x in ('event', 'fest', 'wild area', 'spotlight', 'research day', 'tour', 'evento', 'season')): return 'Eventi'
    return 'Altro'

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return BeautifulSoup(r.read(), 'html.parser')

def parse_page(soup):
    items = []
    seen = set()
    for a in soup.select('a[href]'):
        href = urljoin(BASE, a.get('href', ''))
        path = urlparse(href).path
        if not re.search(r'/(?:post|news)/[^/]+', path) or path.rstrip('/') in ('/news', '/en/news'):
            continue
        if urlparse(href).netloc not in ('pokemongolive.com', 'www.pokemongolive.com'):
            continue
        title = ' '.join(a.stripped_strings)
        if len(title) < 12 or len(title) > 240 or href in seen:
            continue
        seen.add(href)
        items.append({'title': title, 'url': href, 'category': category(title), 'published': '', 'summary': ''})
    return items

def main():
    found = []
    for page in PAGES:
        try:
            found = parse_page(fetch(page))
            print(f'{page}: {len(found)} annunci')
            if found: break
        except Exception as exc:
            print(f'Errore {page}: {exc}')
    if not found:
        raise RuntimeError('Nessun annuncio ufficiale trovato: mantengo il feed precedente senza sovrascriverlo.')
    # Non dedurre la data dell'evento dalla data dell'articolo.
    payload = {'updated_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'items': found[:80]}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Salvati {len(payload["items"])} annunci')

if __name__ == '__main__':
    main()
