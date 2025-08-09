#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SKRYPT 12: Przetwarzacz Danych (process_data.py) - WERSJA FINALNA (BEZ OPÓŹNIEŃ)

Cel:
  - Wersja zoptymalizowana pod kątem szybkości, z usuniętym opóźnieniem między zapytaniami.
  - Zachowuje wszystkie poprawki dotyczące parsowania, czyszczenia danych i logowania błędów.
"""
import os
import re
import json
import requests
from bs4 import BeautifulSoup
from time import sleep
from typing import List, Dict, Optional, Tuple
import random
from collections import defaultdict

# --- Konfiguracja Globalna ---
BASE_URL = "https://liturgia.wiara.pl"
ROOT_DIR = "Lekcjonarz_JSON_Finalny"
JOBS_FILE = "jobs.json"
ERRORS_FILE = "errors.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
}
# MIN_DELAY I MAX_DELAY NIE SĄ JUŻ UŻYWANE
# MIN_DELAY = 0.8
# MAX_DELAY = 2.2

SPECIAL_CASES_KEYWORDS = {
    "Wigilia-Paschalna": "Wigilia Paschalna w Wielką Noc",
    "Wigilia-Zeslania-Ducha-Swietego": "Wigilia Zesłania Ducha Świętego",
    "Wniebowziecie": "Uroczystość Wniebowzięcia NMP"
}
# Lista fraz wprowadzających do usunięcia
PHRASES_TO_REMOVE = [
    "Czytanie z ", "Słowa Ewangelii według "
]

def sanitize_name(text: str) -> str:
    """Oczyszcza tekst na potrzeby nazwy pliku/folderu."""
    text = text.replace(' ', '_').replace(',', '').replace('.', '')
    text = re.sub(r'[-/\\:*"<>|?]', '_', text)
    return text

def is_sigla(text: str) -> bool:
    """Ulepszona funkcja heurystyczna do identyfikacji sigli biblijnych."""
    text = text.strip()
    if not text or len(text) > 150 or '\n' in text: return False
    if not re.search(r'\d', text): return False
    if len(text.split()) > 10: return False
    if not (re.search(r'[a-zA-Z]', text) and re.search(r'\d', text)): return False
    return True

def parse_modern_layout(container: BeautifulSoup) -> List[Dict]:
    """Parser dla stron o nowoczesnej strukturze ('block-title')."""
    all_readings = []
    reading_titles = container.find_all(["p", "h3"], class_="block-title")

    for title_tag in reading_titles:
        typ = title_tag.get_text(strip=True)
        if "ŚPIEW PRZED EWANGELIĄ" in typ.upper(): typ = "AKLAMACJA"

        current_reading = {"typ": typ, "sigla": "", "opis": "", "tekst": ""}
        
        current_element = title_tag
        next_el = current_element.find_next_sibling()
        if next_el and next_el.name == 'p' and is_sigla(next_el.get_text(strip=True)):
             current_reading['sigla'] = next_el.get_text(strip=True)
             current_element = next_el

        while current_element := current_element.find_next_sibling():
            if 'block-title' in current_element.get('class', []): break
            if not hasattr(current_element, 'name') or current_element.name != 'p': continue
            
            p_clone = BeautifulSoup(str(current_element), 'html.parser').p
            if not p_clone: continue

            if not current_reading['sigla'] and 'bible-verse' in p_clone.get('class', []):
                current_reading['sigla'] = p_clone.get_text(strip=True)
                continue

            opis_tag = p_clone.find(['em', 'i', 'b'])
            if opis_tag and not current_reading['opis']:
                current_reading['opis'] = opis_tag.get_text(strip=True)
                opis_tag.decompose()
            
            for br in p_clone.find_all("br"): br.replace_with("\n")
            current_reading["tekst"] += p_clone.get_text() + '\n'
        
        all_readings.append(current_reading)
    return all_readings

def parse_legacy_layout(container: BeautifulSoup) -> List[Dict]:
    """Parser dla stron o starszej, prostej strukturze (tytuł w <strong>)."""
    all_readings = []
    for br in container.find_all("br"): br.replace_with("\n")
    paragraphs = container.find_all(['p', 'div']) # Szersze wyszukiwanie
    
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        
        if p.find('strong'):
            lines = p.get_text('\n').split('\n')
            typ = lines[0].strip().upper()
            if "ŚPIEW PRZED EWANGELIĄ" in typ: typ = "AKLAMACJA"
            if "PSALM RESPONSORYJNY" in typ: typ = "PSALM RESPONSORYJNY"

            current_reading = {"typ": typ, "sigla": "", "opis": "", "tekst": ""}
            
            if len(lines) > 1 and is_sigla(lines[1]):
                current_reading['sigla'] = lines[1].strip()
            
            i += 1
            if not current_reading['sigla'] and i < len(paragraphs) and is_sigla(paragraphs[i].get_text(strip=True)):
                current_reading['sigla'] = paragraphs[i].get_text(strip=True)
                i += 1

            while i < len(paragraphs) and not paragraphs[i].find('strong'):
                p_content = paragraphs[i]
                if p_content.find('em') and not current_reading['opis']:
                    current_reading['opis'] = p_content.get_text(strip=True)
                current_reading['tekst'] += p_content.get_text() + '\n'
                i += 1
            
            all_readings.append(current_reading)
        else:
            i += 1
    return all_readings

def finalize_readings(readings: List[Dict]) -> List[Dict]:
    """Wykonuje finalne czyszczenie: usuwa niechciane frazy, formatuje Aklamacje, konsoliduje Psalmy."""
    if not readings: return []

    final_readings = []
    for r in readings:
        if not r.get('typ'): continue # Pomiń puste obiekty

        if r['sigla'] and r['sigla'] in r['tekst']:
            r['tekst'] = r['tekst'].replace(r['sigla'], '')
        if r['opis'] and r['opis'] in r['tekst']:
            r['tekst'] = r['tekst'].replace(r['opis'], '')

        lines = r['tekst'].split('\n')
        clean_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line: continue
            if any(stripped_line.startswith(phrase) for phrase in PHRASES_TO_REMOVE):
                continue
            
            if "PSALM" in r['typ'].upper() and stripped_line.isupper() and len(stripped_line.split()) < 5:
                 stripped_line = stripped_line.title()

            if "albo: Alleluja" in stripped_line:
                r['opis'] = r.get('opis', '') + ' (albo: Alleluja)'
                continue

            clean_lines.append(stripped_line)

        r['tekst'] = '\n'.join(clean_lines).strip()
        final_readings.append(r)

    consolidated_list, buffer = [], None
    acclamation_pattern = re.compile(r'^(Aklamacja:?\s*)?(Alleluja,?\s*)+(\.)?$', re.IGNORECASE)
    desired_description = "Aklamacja: Alleluja, alleluja, alleluja."

    for r in final_readings:
        typ = r['typ'].upper()
        is_psalm_part = "PSALM" in typ or "REFREN" in typ
        is_acclamation_part = "AKLAMACJA" in typ or "ALLELUJA" in typ
        
        # Nowa, precyzyjna obsługa aklamacji
        if r['typ'] == "AKLAMACJA":
            text_lines = r['tekst'].split('\n')
            clean_text = []
            found_pattern = False
            for line in text_lines:
                if acclamation_pattern.match(line.strip()):
                    found_pattern = True
                else:
                    clean_text.append(line)
            if found_pattern:
                r['opis'] = desired_description
                r['tekst'] = '\n'.join(clean_text).strip()


        if is_psalm_part:
            if not buffer:
                buffer = r
                buffer['typ'] = "PSALM RESPONSORYJNY"
            else:
                buffer['tekst'] += '\n' + r['typ'] + '\n' + r['tekst']
        else:
            if buffer: consolidated_list.append(buffer); buffer = None
            consolidated_list.append(r)
    if buffer: consolidated_list.append(buffer)
    
    return consolidated_list

def process_page(session: requests.Session, page_url: str) -> Optional[Dict]:
    """Pobiera i parsuje dane, wybierając odpowiednią, stabilną metodę."""
    try:
        response = session.get(page_url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e: return {"error": str(e)}

    article_container = soup.select_one("div.cf.txt")
    if not article_container: return {"error": "Nie znaleziono kontenera <div class='cf txt'>."}

    page_title_tag = article_container.find("h1")
    page_title = page_title_tag.get_text(strip=True) if page_title_tag else "Brak tytułu"

    content_container = article_container.find("div", class_="txt__rich-area")
    if not content_container: return {"error": "Brak kontenera treści."}
    
    for unwanted in content_container.select('.content_index, span.content_index_elemenet, .doc_content_video_preview, span[style*="font-size:11px"]'):
        unwanted.decompose()

    if content_container.find(class_="block-title"):
        all_readings = parse_modern_layout(content_container)
    else:
        all_readings = parse_legacy_layout(content_container)

    if not all_readings:
        return {"error": "Nie udało się sparsować czytań."}
    
    final_readings = finalize_readings(all_readings)
    return {"data": {"page_title": page_title, "readings": final_readings}}

def main():
    print("Rozpoczynanie pracy OSTATECZNEGO skryptu (v12 - BEZ OPÓŹNIEŃ)...")
    os.makedirs(ROOT_DIR, exist_ok=True)

    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            jobs_to_process: List[Tuple[str, str]] = json.load(f)
    except FileNotFoundError:
        print(f"[BŁĄD] Plik '{JOBS_FILE}' nie istnieje."); return

    failed_jobs = []
    with requests.Session() as session:
        session.headers.update(HEADERS)
        
        total_jobs = len(jobs_to_process)
        for i, (folder_name, page_url) in enumerate(jobs_to_process, 1):
            # ZAKOMENTOWANA LINIA ODPOWIEDZIALNA ZA OPÓŹNIENIE
            # sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            print(f"[{i}/{total_jobs}] Pobieranie: {page_url.replace(BASE_URL, '')}")
            try:
                result = process_page(session, page_url)
                if result and "data" in result and result["data"].get("readings"):
                    day_data = result["data"]
                    dir_path = os.path.join(ROOT_DIR, sanitize_name(folder_name))
                    os.makedirs(dir_path, exist_ok=True)
                    filepath = os.path.join(dir_path, sanitize_name(day_data['page_title']) + ".json")
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump({"url": page_url, "tytul_dnia": day_data['page_title'], "czytania": day_data['readings']}, f, ensure_ascii=False, indent=2)
                else:
                    error_msg = result.get('error', 'Brak danych') if result else "Brak danych"
                    print(f"  [BŁĄD] Nie udało się przetworzyć. Powód: {error_msg}")
                    failed_jobs.append([folder_name, page_url])
            except Exception as e:
                print(f"  [KRYTYCZNY BŁĄD] Wystąpił nieoczekiwany błąd: {e}")
                failed_jobs.append([folder_name, page_url])

    processed_count = total_jobs - len(failed_jobs)
    print("\n--- ZAKOŃCZONO PRZETWARZANIE ---")
    print(f"Pomyślnie przetworzono dane z {processed_count} stron.")
    print(f"Liczba stron, których nie udało się pobrać: {len(failed_jobs)}.")
    
    if failed_jobs:
        print(f"Zapisywanie listy nieudanych prób do pliku: {ERRORS_FILE}")
        with open(ERRORS_FILE, "w", encoding="utf-8") as f:
            json.dump(failed_jobs, f, ensure_ascii=False, indent=2)
    
    print(f"Wszystkie dane zostały zapisane w katalogu: {ROOT_DIR}")

if __name__ == "__main__":
    main()