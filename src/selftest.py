# -*- coding: utf-8 -*-
import os, requests
from dotenv import load_dotenv
from src.offers_fetcher import fetch_offers

def has_affiliate(url: str) -> bool:
    return "matt_word=" in url and "matt_tool=" in url

def main():
    load_dotenv()
    items = fetch_offers(max_pages=1)
    print("Muestra:", len(items), "items")
    for it in items[:5]:
        url = it["permalink"]
        print("\nTITLE:", it["title"][:80])
        print("URL   :", url)
        print("AFF   :", "OK" if has_affiliate(url) else "MISSING")
        try:
            r = requests.head(url, allow_redirects=True, timeout=10)
            print("FINAL :", r.url[:140])
        except Exception as e:
            print("HEAD error:", e)

if __name__ == "__main__":
    main()
