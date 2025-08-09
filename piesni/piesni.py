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
TIMEOUT_SECONDS = 15

def parse_page_content(page_source: str) -> list:
    """
    Ujednolicona, elastyczna funkcja parsująca, która obsługuje obie znane struktury HTML
    ze szczegółowym logowaniem.
    """
    soup = BeautifulSoup(page_source, 'html.parser')
    content_container = soup.find('div', class_='txt__rich-area')

    if not content_container:
        print("    [DIAGNOZA-BŁĄD] Nie znaleziono kontenera 'txt__rich-area'.")
        return []
        
    print("\n--- DIAGNOSTYKA: Zawartość kontenera 'txt__rich-area' ---")
    print(content_container.prettify())
    print("--- KONIEC DIAGNOSTYKI ---\n")

    suggestions = []
    current_moment = {}

    for element in content_container.find_all(['h3', 'div', 'p'], recursive=False):
        if not isinstance(element, Tag):
            continue
        
        element_text = element.get_text(strip=True)
        print(f"\n    ---> Analizuję element <{element.name}> o treści: '{element_text[:80]}...'")
        
        is_new_moment = False
        moment_text = ""
        if element.name == 'h3':
            is_new_moment = True
            moment_text = element_text
        elif element.find('u'):
            is_new_moment = True
            moment_text = element_text

        if is_new_moment:
            if current_moment and current_moment.get("piesni"):
                suggestions.append(current_moment)
            current_moment = {"moment": moment_text, "piesni": []}
            print(f"    [DECYZJA] Znaleziono NOWY MOMENT: '{moment_text}'")
            continue
            
        if not current_moment:
            continue
            
        if element.find('strong'):
            song_text = element_text
            current_moment["piesni"].append(song_text)
            print(f"    [DECYZJA] To jest PIEŚŃ. Dodaję: '{song_text}'")
        elif element.find('em'):
            opis_text = element_text
            current_moment["opis"] = opis_text
            print(f"    [DECYZJA] To jest OPIS. Dodaję: '{opis_text[:60]}...'")
        elif not element_text:
            print(f"    [IGNORE] Pomijam pusty element.")
        else:
            print(f"    [IGNORE] Pomijam niepasujący element.")

    if current_moment and current_moment.get("piesni"):
        suggestions.append(current_moment)

    return suggestions

def main():
    print("--- START SKRYPTU POBIERAJĄCEGO SUGESTIE (v. Finalna 3.0) ---")

    if not os.path.exists(INPUT_FILE):
        print(f"[BŁĄD] Plik '{INPUT_FILE}' nie istnieje.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f: links_to_process = json.load(f)
    print(f"[INFO] Znaleziono {len(links_to_process)} linków do przetworzenia.")

    print("[INFO] Konfiguracja przeglądarki Chrome...")
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
            print(f"[INFO] Otwieram stronę: '{day_name}' | URL: {page_url}")

            driver.get(page_url)
            
            # --- KLUCZOWY KROK: Obsługa banera RODO ---
            try:
                print("  [AKCJA] Oczekiwanie na przycisk zgody RODO...")
                consent_button_xpath = "//button[contains(., 'AKCEPTUJĘ I PRZECHODZĘ DO SERWISU')]"
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, consent_button_xpath))).click()
                print("  [OK] Przycisk RODO został znaleziony i kliknięty.")
                time.sleep(2) # Czas na przeładowanie strony po akceptacji
            except Exception:
                print("  [INFO] Baner RODO nie pojawił się lub został obsłużony inaczej.")

            print(f"  [INFO] Oczekiwanie na załadowanie treści w 'txt__rich-area'...")
            WebDriverWait(driver, TIMEOUT_SECONDS).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.txt__rich-area > *'))
            )
            print(f"  [OK] Treść strony została załadowana.")
            
            suggestions = parse_page_content(driver.page_source)
            
            if not suggestions:
                print("  [BŁĄD] Nie udało się wyodrębnić żadnych sugestii ze strony.")
                all_song_suggestions.append({"nazwa": day_name, "link": page_url, "sugestie": [{"error": "Parsowanie nie zwróciło danych"}]})
                continue

            final_suggestions = []
            for moment_data in suggestions:
                if not moment_data.get("piesni"):
                    continue
                moment_obj = {"moment": moment_data.get("moment")}
                for j, song in enumerate(moment_data.get("piesni", []), 1):
                    moment_obj[f"piesn_{j}"] = song
                if "opis" in moment_data:
                    moment_obj["opis"] = moment_data["opis"]
                final_suggestions.append(moment_obj)

            print(f"  [SUKCES] Pomyślnie przetworzono {len(final_suggestions)} momentów.")
            all_song_suggestions.append({"nazwa": day_name, "link": page_url, "sugestie": final_suggestions})

        except Exception as e:
            print(f"  [BŁĄD KRYTYCZNY] Wystąpił nieoczekiwany błąd: {e}")
            all_song_suggestions.append({"nazwa": day_name, "link": page_url, "sugestie": [{"error": str(e)}]})

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