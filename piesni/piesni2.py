import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, Tag

# --- Konfiguracja ---
INPUT_FILE = "piesni_podloga_linki.json"
OUTPUT_FILE = "propozycje_piesni.json"
TIMEOUT_SECONDS = 10 # Czas oczekiwania na załadowanie elementów strony

def parse_page_content(page_source: str) -> list:
    """
    Ujednolicona funkcja parsująca, która obsługuje obie znane struktury HTML.
    """
    soup = BeautifulSoup(page_source, 'html.parser')
    content_container = soup.find('div', class_='txt__rich-area')

    if not content_container:
        print("    [DIAGNOZA-BŁĄD] Nie znaleziono kontenera 'txt__rich-area' w kodzie strony po załadowaniu.")
        return []
        
    print("\n--- DIAGNOSTYKA: Zawartość kontenera 'txt__rich-area' po renderowaniu przez przeglądarkę ---")
    print(content_container.prettify())
    print("--- KONIEC DIAGNOSTYKI ---\n")

    suggestions = []
    current_moment = {}

    # Iterujemy po wszystkich bezpośrednich dzieciach kontenera, niezależnie od tagu
    for element in content_container.children:
        if not isinstance(element, Tag):
            continue

        # Wariant 1: Moment w nagłówku H3 (nowsze strony)
        if element.name == 'h3':
            if current_moment: suggestions.append(current_moment)
            moment_text = element.get_text(strip=True)
            current_moment = {"moment": moment_text, "piesni": []}
            print(f"    [LOG] Znaleziono Moment (H3): '{moment_text}'")
            continue
        
        # Wariant 2: Moment w paragrafie z podkreśleniem (starsze strony)
        u_tag = element.find('u')
        if u_tag:
            if current_moment: suggestions.append(current_moment)
            moment_text = element.get_text(strip=True)
            current_moment = {"moment": moment_text, "piesni": []}
            print(f"    [LOG] Znaleziono Moment (P z U): '{moment_text}'")
            continue

        # Jeśli nie jesteśmy wewnątrz żadnego "momentu", ignorujemy element
        if not current_moment:
            print(f"    [IGNORE] Pomijam element '{element.get_text(strip=True)[:50]}...' (brak aktywnego momentu).")
            continue
            
        # Szukanie pieśni i opisów
        strong_tag = element.find('strong')
        em_tag = element.find('em')
        
        if strong_tag:
            song_text = element.get_text(strip=True)
            current_moment["piesni"].append(song_text)
            print(f"      [LOG] Dodano Pieśń: '{song_text}'")
        elif em_tag:
            opis_text = element.get_text(strip=True)
            current_moment["opis"] = opis_text
            print(f"      [LOG] Dodano Opis: '{opis_text[:50]}...'")
        else:
             # Ignorowanie pustych tagów, separatorów i innych niepasujących
             if element.get_text(strip=True) != "":
                print(f"    [IGNORE] Pomijam niepasujący element: '{element.get_text(strip=True)[:50]}...'")

    if current_moment:
        suggestions.append(current_moment)

    return suggestions

def main():
    print("--- START SKRYPTU POBIERAJĄCEGO SUGESTIE (v. Finalna - Selenium) ---")

    if not os.path.exists(INPUT_FILE):
        print(f"[BŁĄD] Plik '{INPUT_FILE}' nie istnieje.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f: links_to_process = json.load(f)
    print(f"[INFO] Znaleziono {len(links_to_process)} linków do przetworzenia.")

    print("[INFO] Konfiguracja przeglądarki Chrome w tle...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("window-size=1920,1080")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("[OK] Przeglądarka uruchomiona.")
    except Exception as e:
        print(f"[BŁĄD KRYTYCZNY] Nie udało się uruchomić przeglądarki: {e}")
        return

    all_song_suggestions = []
    for i, day_data in enumerate(links_to_process, 1):
        print(f"\n{'='*20} Przetwarzanie {i}/{len(links_to_process)} {'='*20}")
        
        try:
            page_url = day_data['link']
            day_name = day_data['nazwa']
            print(f"[INFO] Otwieram stronę: '{day_name}'")
            print(f"[URL] {page_url}")

            driver.get(page_url)
            WebDriverWait(driver, TIMEOUT_SECONDS).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'txt__rich-area'))
            )
            print(f"  [OK] Strona załadowana. Oczekiwanie 2s na pełne wykonanie skryptów...")
            time.sleep(2)

            suggestions = parse_page_content(driver.page_source)
            
            if not suggestions:
                print("  [BŁĄD] Nie udało się wyodrębnić żadnych sugestii ze strony.")
                all_song_suggestions.append({"nazwa": day_name, "sugestie": [{"error": "Parsowanie nie zwróciło danych"}]})
                continue

            final_suggestions = []
            for moment_data in suggestions:
                if not moment_data.get("piesni"):
                    print(f"    [FINAL-WARN] Moment '{moment_data.get('moment')}' nie zawiera pieśni. Pomijam.")
                    continue
                moment_obj = {"moment": moment_data.get("moment")}
                for j, song in enumerate(moment_data.get("piesni", []), 1):
                    moment_obj[f"piesn_{j}"] = song
                if "opis" in moment_data:
                    moment_obj["opis"] = moment_data["opis"]
                final_suggestions.append(moment_obj)

            print(f"  [SUKCES] Pomyślnie przetworzono {len(final_suggestions)} momentów.")
            all_song_suggestions.append({"nazwa": day_name, "sugestie": final_suggestions})

        except Exception as e:
            print(f"  [BŁĄD KRYTYCZNY] Wystąpił nieoczekiwany błąd: {e}")
            all_song_suggestions.append({"nazwa": day_name, "sugestie": [{"error": str(e)}]})

    driver.quit()
    print("\n[INFO] Przeglądarka została zamknięta.")

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_song_suggestions, f, ensure_ascii=False, indent=4)
        print(f"\n[ZAKOŃCZONO] Pomyślnie zapisano wszystkie dane do pliku: {OUTPUT_FILE}")
    except IOError as e:
        print(f"[BŁĄD KRYTYCZNY] Nie udało się zapisać pliku: {e}")

if __name__ == "__main__":
    main()