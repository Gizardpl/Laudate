#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from time import sleep
from typing import List, Tuple, Set

# --- Konfiguracja Globalna ---
BASE_URL = "https://liturgia.wiara.pl"
NAVIGATOR_URL = urljoin(BASE_URL, "/Czytania_mszalne/Nawigator")
JOBS_FILE = "jobs.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
}

def sanitize_name(text: str) -> str:
    """Oczyszcza tekst na potrzeby nazwy folderu, zachowując cyfry rzymskie."""
    text = text.replace(' ', '_').replace(',', '').replace('.', '')
    text = text.replace('Nawigator_-_', '').replace('Czytania_na_', '')
    text = re.sub(r'[-/\\:*"<>|?]', '_', text)
    return text

def discover_base_links(session: requests.Session) -> List[Tuple[str, str]]:
    print("--- ETAP 1: Szybkie skanowanie nawigacji ---")
    base_day_links: List[Tuple[str, str]] = []
    pages_to_scan: List[Tuple[str, str]] = [(NAVIGATOR_URL, "Okres_Glowny")]
    scanned_pages: Set[str] = set()

    while pages_to_scan:
        current_url, current_folder = pages_to_scan.pop(0)
        if current_url in scanned_pages: continue
        scanned_pages.add(current_url)
        print(f"\rSkanowanie: {current_url.replace(BASE_URL, '')}", end="", flush=True)

        try:
            response = session.get(current_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except requests.RequestException: continue

        nav_containers = soup.find_all("div", class_=["menu_vert_open_w", "dirstree", "doc_content"])
        
        for container in nav_containers:
            for link in container.find_all("a", href=True):
                href, full_url = link.get('href', ''), urljoin(BASE_URL, link.get('href', ''))
                if '/Czytania_mszalne/Nawigator/' in href and full_url not in scanned_pages:
                    pages_to_scan.append((full_url, sanitize_name(link.get_text(strip=True))))
                elif "/doc/" in href and not any(item[1] == full_url for item in base_day_links):
                    base_day_links.append((current_folder, full_url))
    
    print(f"\nZakończono skanowanie. Znaleziono {len(base_day_links)} głównych stron do dalszej analizy.")
    return base_day_links

def expand_and_filter_subpages(session: requests.Session, base_links: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    print("\n--- ETAP 2: Analiza podstron, filtrowanie i usuwanie duplikatów ---")
    final_jobs: List[Tuple[str, str]] = []
    
    special_cases = ["Wigilia-Paschalna", "Wigilia-Zeslania-Ducha", "Wniebowziecie"]

    for i, (folder_name, url) in enumerate(base_links, 1):
        print(f"\rAnalizowanie linku {i}/{len(base_links)}: {url.replace(BASE_URL, '')}", end="", flush=True)
        try:
            sleep(0.1)
            response = session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            pager = soup.find("div", class_="pgr")
            if pager:
                page_links = {urljoin(BASE_URL, a['href']) for a in pager.find_all("a", href=True)}
                page_links.add(url)
                
                def sort_key(link):
                    match = re.search(r'/(\d+)$', link)
                    return int(match.group(1)) if match else 0

                sorted_pages = sorted(list(page_links), key=sort_key)
                is_special_case = any(case in url for case in special_cases)

                if is_special_case:
                    final_jobs.extend([(folder_name, page) for page in sorted_pages])
                else:
                    pages_to_keep = []
                    last_page_index = len(sorted_pages) - 1
                    for index, page_link in enumerate(sorted_pages):
                        page_num = sort_key(page_link)
                        if page_num > 0 and page_num % 2 == 0: continue
                        if index == last_page_index and page_num % 2 != 0: continue
                        pages_to_keep.append(page_link)
                    final_jobs.extend([(folder_name, page) for page in pages_to_keep])
            else:
                final_jobs.append((folder_name, url))
        except requests.RequestException: continue
            
    unique_jobs = sorted(list(set(final_jobs)))
    print(f"\nZakończono analizę. Znaleziono {len(unique_jobs)} unikalnych stron z tekstem do pobrania.")
    return unique_jobs

def main():
    print("Rozpoczynanie pracy skryptu odkrywającego linki...")
    with requests.Session() as session:
        session.headers.update(HEADERS)
        base_links = discover_base_links(session)
        if not base_links: return
        jobs_to_process = expand_and_filter_subpages(session, base_links)
        if not jobs_to_process: return
        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs_to_process, f, ensure_ascii=False, indent=2)
        print(f"\n--- ZAKOŃCZONO ODKRYWANIE ---")
        print(f"Pomyślnie zapisano {len(jobs_to_process)} linków do pliku: {JOBS_FILE}")

if __name__ == "__main__":
    main()