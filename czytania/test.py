#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SKRYPT 2: Przetwarzacz Danych (process_data.py) - WERSJA FINALNA

Cel:
  - Wczytuje listę linków z pliku `jobs.json`.
  - Obsługuje specjalne przypadki (np. Wigilia Paschalna), łącząc dane z wielu stron w jeden plik.
  - Implementuje DWIE strategie parsowania, automatycznie wybierając właściwą.
  - Inteligentnie konsoliduje wszystkie części psalmu w jeden obiekt.
  - Precyzyjnie wyodrębnia 'typ', 'sigla', 'opis' i 'tekst', ignorując niechciane paragrafy.
  - Zapisuje dane w docelowej strukturze folderów i plików, zachowując oryginalne nazewnictwo.
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
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
}
MIN_DELAY = 0.8
MAX_DELAY = 2.2

# Słowa kluczowe do grupowania linków
SPECIAL_CASES_KEYWORDS = {
    "Wigilia-Paschalna": "Wigilia Paschalna w Wielką Noc",
    "Wigilia-Zeslania-Ducha-Swietego": "Wigilia Zesłania Ducha Świętego",
    "Wniebowziecie": "Uroczystość Wniebowzięcia NMP"
}

def sanitize_name(text: str) -> str:
    """Oczyszcza tekst na potrzeby nazwy pliku/folderu."""
    text = text.replace(' ', '_').replace(',', '').replace('.', '')
    text = re.sub(r'[-/\\:*"<>|?]', '_', text)
    return text

def consolidate_psalm(readings: List[Dict]) -> List[Dict]:
    """Przegląda listę czytań i łączy wszystkie części psalmu w jeden obiekt."""
    new_readings = []
    psalm_buffer = None
    
    for reading in readings:
        typ = reading.get("typ", "").upper()
        is_psalm_part = "PSALM" in typ or typ.startswith("REFREN")
        
        if is_psalm_part:
            if not psalm_buffer:
                psalm_buffer = {"typ": "PSALM RESPONSORYJNY", "sigla": "", "opis": "", "tekst": ""}
            if not psalm_buffer["sigla"] and reading.get("sigla"):
                psalm_buffer["sigla"] = reading["sigla"]
            
            text_to_add = reading.get("tekst", "")
            if psalm_buffer["tekst"] and text_to_add:
                psalm_buffer["tekst"] += "\n" + text_to_add
            elif text_to_add:
                psalm_buffer["tekst"] += text_to_add
        else:
            if psalm_buffer:
                new_readings.append(psalm_buffer)
                psalm_buffer = None
            new_readings.append(reading)
            
    if psalm_buffer:
        new_readings.append(psalm_buffer)
    return new_readings

def parse_with_fallback_method(container: BeautifulSoup) -> List[Dict]:
    """Alternatywna, sprawdzona metoda parsowania dla stron o starszej strukturze HTML."""
    all_readings = []
    
    rich_text_area = container.find('div', class_='txt__rich-area')
    if not rich_text_area: return []

    # Usuwamy niechciane elementy na starcie
    if rich_text_area.find('div', class_='content_index'):
        rich_text_area.find('div', class_='content_index').decompose()
    if rich_text_area.find('p'):
        first_p = rich_text_area.find('p')
        if "Liturgia Słowa" in first_p.get_text():
            first_p.decompose()

    for br in rich_text_area.find_all("br"):
        br.replace_with("\n")

    all_paragraphs = rich_text_area.find_all('p', recursive=False)
    
    i = 0
    while i < len(all_paragraphs):
        p = all_paragraphs[i]
        
        if p.find('strong'):
            full_title_text = p.get_text('\n', strip=True).split('\n')
            typ = full_title_text[0].upper()
            if "ŚPIEW PRZED EWANGELIĄ" in typ: typ = "AKLAMACJA"

            current_reading = {
                "typ": typ,
                "sigla": full_title_text[1] if len(full_title_text) > 1 else "",
                "opis": "", "tekst": ""
            }
            i += 1
            
            text_parts = []
            
            # Pętla zbierająca dane dla jednego czytania
            while i < len(all_paragraphs):
                p_content = all_paragraphs[i]
                if p_content.find('strong'): break # Koniec, bo to następny tytuł

                # Pominięcie paragrafów ze stylem font-size: smaller
                if p_content.find('span', style=lambda s: s and 'font-size: smaller' in s):
                    i += 1
                    continue
                
                # Zbieranie opisu
                if p_content.find('em') and not current_reading['opis']:
                    current_reading['opis'] = p_content.get_text(strip=True)
                # Pominięcie wprowadzenia
                elif 'Czytanie z' not in p_content.get_text() and 'Słowa Ewangelii' not in p_content.get_text():
                    text_parts.append(p_content.get_text())

                # Sprawdzenie końca czytania
                if "Oto słowo Boże" in p_content.get_text() or "Oto słowo Pańskie" in p_content.get_text():
                    i += 1
                    break
                i += 1
            
            if any(k in typ for k in ["PSALM", "REFREN", "AKLAMACJA"]):
                current_reading['tekst'] = "\n".join(part.strip() for part in text_parts if part.strip())
            else:
                current_reading['tekst'] = " ".join(part.strip() for part in text_parts if part.strip())
            
            all_readings.append(current_reading)
        else:
            i += 1
            
    return all_readings

def parse_with_primary_method(container: BeautifulSoup) -> List[Dict]:
    """Główna metoda parsowania dla stron z klasą 'block-title'."""
    all_readings = []
    reading_titles = container.find_all("p", class_="block-title")

    for title_tag in reading_titles:
        typ = title_tag.get_text(strip=True)
        if "ŚPIEW PRZED EWANGELIĄ" in typ: typ = "AKLAMACJA"

        current_reading = {"typ": typ, "sigla": "", "opis": "", "tekst": ""}
        text_parts = []
        current_element = title_tag

        while current_element := current_element.find_next_sibling():
            if 'block-title' in current_element.get('class', []): break
            if not hasattr(current_element, 'name'): continue
            
            if current_element.find('span', style=lambda s: s and 'font-size: smaller' in s):
                continue
            
            if 'bible-verse' in current_element.get('class', []):
                current_reading["sigla"] = current_element.get_text(strip=True)
            elif current_element.name == 'p' and current_element.find('em'):
                current_reading["opis"] = current_element.get_text(strip=True)
            elif 'indent' in current_element.get('class', []):
                if "Czytanie z" in current_element.get_text() or "Słowa Ewangelii" in current_element.get_text(): continue
                
                for br in current_element.find_all("br"):
                    br.replace_with("\n")
                text_parts.append(current_element.get_text())
        
        typ_upper = current_reading['typ'].upper()
        if any(k in typ_upper for k in ["PSALM", "REFREN", "AKLAMACJA"]):
             current_reading["tekst"] = "\n".join(part.strip() for part in text_parts if part.strip())
        else:
             current_reading["tekst"] = " ".join(part.strip() for part in text_parts if part.strip())
        
        all_readings.append(current_reading)
        
    return all_readings

def process_page(session: requests.Session, page_url: str) -> Optional[Dict]:
    """Pobiera i parsuje dane, automatycznie wybierając właściwą metodę."""
    try:
        response = session.get(page_url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e: return {"error": str(e)}

    article_container = soup.select_one("div.cf.txt")
    if not article_container: return {"error": "Nie znaleziono kontenera <div class='cf txt'>."}

    page_title_tag = article_container.find("h1")
    if not page_title_tag: return {"error": "Nie znaleziono nagłówka H1."}
    page_title = page_title_tag.get_text(strip=True)

    content_container = article_container.find("div", class_="txt__content")
    if not content_container: return {"error": "Brak kontenera <div class='txt__content'>."}
    if content_container.find("span", class_="content_ext_plugin"): return {"error": "Strona wideo, pominięto."}

    is_legacy_structure = not content_container.find("p", class_="block-title")
    if is_legacy_structure: print("  [INFO] Wykryto alternatywną strukturę. Używam metody zapasowej.")
    
    all_readings = parse_with_fallback_method(content_container) if is_legacy_structure else parse_with_primary_method(content_container)

    if not all_readings:
        return {"error": "Nie udało się sparsować czytań żadną z metod."}
    
    final_readings = consolidate_psalm(all_readings)
    return {"data": {"page_title": page_title, "readings": final_readings}}

def main():
    print("Rozpoczynanie pracy OSTATECZNEGO skryptu przetwarzającego dane...")
    os.makedirs(ROOT_DIR, exist_ok=True)

    if not os.path.exists(JOBS_FILE):
        print(f"[BŁĄD] Plik '{JOBS_FILE}' nie istnieje."); return

    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        jobs_to_process: List[Tuple[str, str]] = json.load(f)

    grouped_jobs = defaultdict(list)
    for folder_name, url in jobs_to_process:
        special_key = next((key for key in SPECIAL_CASES_KEYWORDS if key in url), None)
        if special_key:
            grouped_jobs[special_key].append((folder_name, url))
        else:
            grouped_jobs[url].append((folder_name, url))

    with requests.Session() as session:
        session.headers.update(HEADERS)
        
        total_groups = len(grouped_jobs)
        processed_pages, failed_pages = 0, 0
        print(f"\n--- ETAP 3: Przetwarzanie {total_groups} zadań ---")

        for i, (group_key, jobs) in enumerate(grouped_jobs.items(), 1):
            
            if group_key in SPECIAL_CASES_KEYWORDS:
                print(f"[{i}/{total_groups}] Przetwarzanie grupy specjalnej: {group_key} ({len(jobs)} stron)")
                all_readings, folder = [], jobs[0][0]
                final_page_title = SPECIAL_CASES_KEYWORDS[group_key]
                
                for job_idx, (_, url) in enumerate(sorted(jobs, key=lambda x: x[1])):
                    # sleep(random.uniform(MIN_DELAY, MAX_DELAY)) # Wyłączone domyślnie
                    print(f"  -> ({job_idx+1}/{len(jobs)}) Pobieranie: {url}")
                    result = process_page(session, url)
                    if result and "data" in result:
                        all_readings.extend(result["data"]["readings"])
                    else:
                        failed_pages += 1
                        print(f"    [INFO] Błąd: {result.get('error', 'Nieznany')}")
                
                if all_readings:
                    processed_pages += len(jobs)
                    final_readings = consolidate_psalm(all_readings)
                    dir_path = os.path.join(ROOT_DIR, sanitize_name(folder))
                    os.makedirs(dir_path, exist_ok=True)
                    filepath = os.path.join(dir_path, sanitize_name(final_page_title) + ".json")
                    json_output = {"url": jobs[0][1], "tytul_dnia": final_page_title, "czytania": final_readings}
                    with open(filepath, "w", encoding="utf-8") as f: json.dump(json_output, f, ensure_ascii=False, indent=2)
            else:
                folder_name, page_url = jobs[0]
                # sleep(random.uniform(MIN_DELAY, MAX_DELAY)) # Wyłączone domyślnie
                print(f"[{i}/{total_groups}] Pobieranie: {page_url.replace(BASE_URL, '')}")
                result = process_page(session, page_url)
                if result and "data" in result:
                    processed_pages += 1
                    day_data = result["data"]
                    dir_path = os.path.join(ROOT_DIR, sanitize_name(folder_name))
                    os.makedirs(dir_path, exist_ok=True)
                    filepath = os.path.join(dir_path, sanitize_name(day_data['page_title']) + ".json")
                    json_output = {"url": page_url, "tytul_dnia": day_data['page_title'], "czytania": day_data['readings']}
                    with open(filepath, "w", encoding="utf-8") as f: json.dump(json_output, f, ensure_ascii=False, indent=2)
                else:
                    failed_pages += 1
                    error_msg = result.get('error', 'Nieznany błąd') if result else "Brak danych"
                    print(f"  [INFO] Nie udało się przetworzyć {page_url}. Powód: {error_msg}")

    print("\n--- ZAKOŃCZONO PRZETWARZANIE ---")
    print(f"Przetworzono pomyślnie dane z {processed_pages} stron.")
    print(f"Liczba stron, których nie udało się pobrać lub zostały pominięte: {failed_pages}.")
    print(f"Wszystkie dane zostały zapisane w katalogu: {ROOT_DIR}")

if __name__ == "__main__":
    main()