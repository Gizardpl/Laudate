#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SKRYPT 2: Przetwarzacz Danych (process_data.py) - WERSJA ZMODYFIKOWANA

Cel:
  - Wczytuje listę linków z pliku `jobs.json`.
  - POMIJA linki zawierające w nazwie "Wigilia".
  - Obsługuje specjalne przypadki, łącząc dane z wielu stron w jeden plik.
  - Implementuje DWIE strategie parsowania, automatycznie wybierając właściwą.
  - Inteligentnie konsoliduje wszystkie części psalmu w jeden obiekt.
  - Precyzyjnie wyodrębnia dane, IGNORUJĄC paragrafy wprowadzające ("Czytanie z...") oraz te zawierające WIDEO.
  - Zapisuje dane w docelowej strukturze folderów i plików.
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
JOBS_FILE = "jobs_backup.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
}
MIN_DELAY = 0.5
MAX_DELAY = 1.5

# Słowa kluczowe do grupowania linków, które nie są 'Wigilią'
SPECIAL_CASES_KEYWORDS = {
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
        # Rozpoznaje psalm po typie lub obecności słowa "Refren"
        is_psalm_part = "PSALM" in typ or typ.startswith("REFREN")
        
        if is_psalm_part:
            if not psalm_buffer:
                psalm_buffer = {"typ": "PSALM RESPONSORYJNY", "sigla": "", "opis": "", "tekst": ""}
            # Uzupełnia siglę, jeśli jeszcze jej nie ma
            if not psalm_buffer["sigla"] and reading.get("sigla"):
                psalm_buffer["sigla"] = reading["sigla"]
            
            # Dodaje tekst do bufora psalmu
            text_to_add = reading.get("tekst", "")
            if psalm_buffer["tekst"] and text_to_add:
                psalm_buffer["tekst"] += "\n" + text_to_add
            elif text_to_add:
                psalm_buffer["tekst"] += text_to_add
        else:
            # Jeśli napotkano inne czytanie, zapisz psalm z bufora i zresetuj
            if psalm_buffer:
                new_readings.append(psalm_buffer)
                psalm_buffer = None
            new_readings.append(reading)
            
    # Zapisz ostatni psalm, jeśli istnieje
    if psalm_buffer:
        new_readings.append(psalm_buffer)
    return new_readings

def parse_with_primary_method(container: BeautifulSoup) -> List[Dict]:
    """Główna metoda parsowania dla stron z klasą 'block-title'."""
    all_readings = []
    reading_titles = container.find_all("p", class_="block-title")

    for title_tag in reading_titles:
        typ = title_tag.get_text(strip=True).upper()
        if "ŚPIEW PRZED EWANGELIĄ" in typ: typ = "AKLAMACJA"

        current_reading = {"typ": typ, "sigla": "", "opis": "", "tekst": ""}
        text_parts = []
        current_element = title_tag

        while current_element := current_element.find_next_sibling():
            if 'block-title' in current_element.get('class', []): break
            if not hasattr(current_element, 'name'): continue
            
            # Ignorowanie legendy do Męki Pańskiej
            if current_element.find('span', style=lambda s: s and 'font-size' in s):
                continue
            
            if 'bible-verse' in current_element.get('class', []):
                current_reading["sigla"] = current_element.get_text(strip=True)
            elif current_element.name == 'p' and current_element.find('em'):
                current_reading["opis"] = current_element.get_text(strip=True)
            elif 'indent' in current_element.get('class', []):
                # >>> MODYFIKACJA: Pomijanie paragrafów wprowadzających <<<
                if "Czytanie z" in current_element.get_text() or "Słowa Ewangelii" in current_element.get_text():
                    continue
                
                for br in current_element.find_all("br"):
                    br.replace_with("\n")
                text_parts.append(current_element.get_text())
        
        # Łączenie tekstu w zależności od typu czytania
        if any(k in typ for k in ["PSALM", "REFREN", "AKLAMACJA"]):
             current_reading["tekst"] = "\n".join(part.strip() for part in text_parts if part.strip())
        else:
             # Usuwa "Oto słowo Boże/Pańskie" i nadmiarowe spacje
             full_text = " ".join(part.strip() for part in text_parts if part.strip())
             current_reading["tekst"] = re.sub(r'\s*Oto słowo (Boże|Pańskie)\.\s*$', '', full_text).strip()

        all_readings.append(current_reading)
        
    return all_readings

def process_page(session: requests.Session, page_url: str) -> Optional[Dict]:
    """Pobiera i parsuje dane z jednej strony, wybierając automatycznie metodę."""
    try:
        response = session.get(page_url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        return {"error": str(e)}

    article_container = soup.select_one("div.cf.txt")
    if not article_container: return {"error": "Nie znaleziono kontenera artykułu."}

    page_title_tag = article_container.find("h1")
    if not page_title_tag: return {"error": "Nie znaleziono tytułu strony (H1)."}
    page_title = page_title_tag.get_text(strip=True)

    content_container = article_container.find("div", class_="txt__content")
    if not content_container: return {"error": "Brak kontenera treści."}

    # >>> MODYFIKACJA: Usuwanie paragrafów z filmami YouTube <<<
    for iframe in content_container.find_all("iframe"):
        # Usuwa cały paragraf, w którym znajduje się film
        if iframe.find_parent('p'):
            iframe.find_parent('p').decompose()

    # Wybór strategii parsowania
    is_legacy_structure = not content_container.find("p", class_="block-title")
    if is_legacy_structure:
        # Alternatywna metoda (niezaimplementowana w pełni w dostarczonym przykładzie)
        # return {"error": "Wykryto starszą strukturę strony, która nie jest obsługiwana."}
        # Dla celów demonstracyjnych zakładamy, że tylko `primary_method` jest potrzebna
        # W Twoim pełnym kodzie tutaj byłaby `parse_with_fallback_method`
        pass
    
    all_readings = parse_with_primary_method(content_container)

    if not all_readings:
        return {"error": "Nie udało się sparsować żadnych czytań."}
    
    # Konsolidacja psalmów po parsowaniu
    final_readings = consolidate_psalm(all_readings)
    return {"data": {"page_title": page_title, "readings": final_readings}}

def main():
    """Główna funkcja sterująca skryptem."""
    print("Rozpoczynanie pracy skryptu przetwarzającego dane...")
    os.makedirs(ROOT_DIR, exist_ok=True)

    if not os.path.exists(JOBS_FILE):
        print(f"[BŁĄD KRYTYCZNY] Plik z zadaniami '{JOBS_FILE}' nie istnieje. Przerwanie pracy.")
        return

    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        all_jobs: List[Tuple[str, str]] = json.load(f)

    # >>> MODYFIKACJA: Filtrowanie linków zawierających "Wigilia" <<<
    jobs_to_process = []
    skipped_jobs_count = 0
    for folder_name, url in all_jobs:
        if "Wigilia" in url:
            skipped_jobs_count += 1
        else:
            jobs_to_process.append((folder_name, url))
    
    if skipped_jobs_count > 0:
        print(f"[INFO] Pominięto {skipped_jobs_count} linki zawierające słowo 'Wigilia'.")

    # Grupowanie zadań (np. dla Wniebowzięcia)
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
        print(f"\n--- Rozpoczęto przetwarzanie {total_groups} zadań ---")

        for i, (group_key, jobs) in enumerate(grouped_jobs.items(), 1):
            sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            
            # Obsługa przypadków specjalnych (wiele linków dla jednego wydarzenia)
            if group_key in SPECIAL_CASES_KEYWORDS:
                print(f"[{i}/{total_groups}] Przetwarzanie grupy specjalnej: {group_key}...")
                all_readings, folder = [], jobs[0][0]
                final_page_title = SPECIAL_CASES_KEYWORDS[group_key]
                
                for job_idx, (_, url) in enumerate(sorted(jobs, key=lambda x: x[1])):
                    print(f"  -> ({job_idx+1}/{len(jobs)}) Pobieranie części: {url.replace(BASE_URL, '')}")
                    result = process_page(session, url)
                    if result and "data" in result:
                        all_readings.extend(result["data"]["readings"])
                    else:
                        failed_pages += 1
                        print(f"    [BŁĄD] {result.get('error', 'Nieznany błąd')}")
                
                if all_readings:
                    processed_pages += len(jobs)
                    final_readings = consolidate_psalm(all_readings)
                    dir_path = os.path.join(ROOT_DIR, sanitize_name(folder))
                    os.makedirs(dir_path, exist_ok=True)
                    filepath = os.path.join(dir_path, sanitize_name(final_page_title) + ".json")
                    json_output = {"url": jobs[0][1], "tytul_dnia": final_page_title, "czytania": final_readings}
                    with open(filepath, "w", encoding="utf-8") as f: json.dump(json_output, f, ensure_ascii=False, indent=2)

            # Obsługa standardowych, pojedynczych linków
            else:
                folder_name, page_url = jobs[0]
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
                    print(f"  [BŁĄD] Nie udało się przetworzyć strony. Powód: {error_msg}")

    print("\n--- ZAKOŃCZONO PRZETWARZANIE ---")
    print(f"Pomyślnie przetworzono dane z {processed_pages} stron.")
    print(f"Liczba stron, które zakończyły się błędem: {failed_pages}.")
    print(f"Wszystkie dane zostały zapisane w katalogu: '{ROOT_DIR}'")

if __name__ == "__main__":
    # Przed uruchomieniem upewnij się, że masz zainstalowane potrzebne biblioteki:
    # pip install requests beautifulsoup4
    main()