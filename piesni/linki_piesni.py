import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- Konfiguracja ---
BASE_URL = "https://liturgia.wiara.pl"
TARGET_URL = urljoin(BASE_URL, "/Propozycje_spiewow")
OUTPUT_FILE = "piesni_podloga_linki.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
}
PREFIX_TO_REMOVE = "Propozycje śpiewów - "

def scrape_song_links():
    """
    Główna funkcja skryptu. Pobiera, parsuje i zapisuje unikalne linki do propozycji śpiewów.
    """
    print("--- START SKRYPTU (wersja z usuwaniem duplikatów) ---")
    print(f"Cel: {TARGET_URL}")

    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        print("\n[LOG] Krok 1: Wysyłanie zapytania GET...")
        response = session.get(TARGET_URL, timeout=20)
        response.raise_for_status()
        print(f"[LOG] Sukces! Otrzymano odpowiedź (status: {response.status_code}).")

    except requests.RequestException as e:
        print(f"[BŁĄD] Nie udało się pobrać strony: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("\n[LOG] Krok 2: Szukanie kontenerów <div class='menu_vert_open_w dirstree'>...")
    containers = soup.find_all('div', class_='menu_vert_open_w dirstree')

    if len(containers) < 2:
        print("[BŁĄD] Nie znaleziono oczekiwanego kontenera z zawartością działu. Struktura strony mogła się zmienić. Przerywam.")
        return
    
    target_container = containers[1]
    print("[LOG] Sukces! Znaleziono kontener z linkami ('Zawartość działu').")

    print("\n[LOG] Krok 3: Szukanie wszystkich linków (tagów <a>) w kontenerze...")
    song_links = target_container.find_all('a')

    if not song_links:
        print("[BŁĄD] Nie znaleziono żadnych linków w docelowym kontenerze. Przerywam.")
        return

    print(f"[LOG] Znaleziono {len(song_links)} linków do przetworzenia. Rozpoczynam filtrowanie duplikatów...")
    
    # KROK 4 (ZMIENIONA LOGIKA): Przetwarzanie linków z pomijaniem duplikatów
    print("\n[LOG] Krok 4: Przetwarzanie linków i zapisywanie unikalnych pozycji...")
    
    results = []
    processed_names = set() # Zbiór do przechowywania nazw, które już zostały dodane

    for i, link_tag in enumerate(song_links, 1):
        if link_tag.has_attr('href'):
            link = urljoin(BASE_URL, link_tag['href'])
            raw_name = link_tag.get_text(strip=True)
            
            # Oczyszczanie nazwy
            if PREFIX_TO_REMOVE in raw_name:
                name = raw_name.replace(PREFIX_TO_REMOVE, "").strip()
            else:
                name = raw_name

            # --- KLUCZOWA ZMIANA: SPRAWDZANIE DUPLIKATÓW ---
            if name not in processed_names:
                # Jeśli nazwa jest nowa, dodajemy ją do wyników i "zapamiętujemy"
                results.append({"nazwa": name, "link": link})
                processed_names.add(name)
                print(f"  - Dodano ({i}/{len(song_links)}): {name}")
            else:
                # Jeśli nazwa już była, pomijamy ją
                print(f"  - DUPLIKAT ({i}/{len(song_links)}): Pomijam '{name}', ponieważ nazwa została już dodana.")
        else:
            print(f"  - Pominięto ({i}/{len(song_links)}): Brak tagu <a> z atrybutem href.")

    # KROK 5: Zapis wyników do pliku JSON
    print("\n[LOG] Krok 5: Zapisywanie wyników do pliku JSON...")
    if not results:
        print("[OSTRZEŻENIE] Brak wyników do zapisania. Plik nie zostanie utworzony.")
        return
        
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"[LOG] Sukces! Pomyślnie zapisano {len(results)} UNIKALNYCH obiektów do pliku: {OUTPUT_FILE}")
    except IOError as e:
        print(f"[BŁĄD] Wystąpił błąd podczas zapisu do pliku {OUTPUT_FILE}: {e}")

    print("\n--- ZAKOŃCZONO PRACĘ SKRYPTU ---")

if __name__ == "__main__":
    scrape_song_links()