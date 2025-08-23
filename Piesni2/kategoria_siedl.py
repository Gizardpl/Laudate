import json
import re
import os

# ==============================================================================
# STAŁE KONFIGURACYJNE
# Zdefiniuj nazwy plików wejściowych i wyjściowych.
# ==============================================================================

# Nazwa pliku wejściowego z pieśniami
PIESNI_INPUT_FILENAME = 'piesni4.json'

# Nazwa pliku z definicjami kategorii
KATEGORIE_FILENAME = 'Kategorie.txt'

# Nazwa pliku wyjściowego, który zostanie utworzony z nowymi danymi
PIESNI_OUTPUT_FILENAME = 'piesni5.json'

# Kodowanie znaków używane w plikach
FILE_ENCODING = 'utf-8'

# Wcięcie dla wynikowego pliku JSON (dla zachowania czytelności)
JSON_INDENTATION = 4


def parse_ranged_kategorie(kategorie_content):
    """
    Przetwarza zawartość pliku z kategoriami i zwraca listę
    kategorii zdefiniowanych przez zakresy numerów.
    """
    ranged_categories = []
    lines = kategorie_content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Dopasowanie wyłącznie dla kategorii z zakresem numerów, np. "1-29 - Adwent {Adw}"
        range_match = re.match(r'(\d+)-(\d+)\s*-\s*(.+?)\s*\{(.+?)\}', line)
        
        if range_match:
            start, end, name, abbr = range_match.groups()
            ranged_categories.append({
                'start': int(start),
                'end': int(end),
                'name': name.strip(),
                'abbr': abbr.strip()
            })
            
    return ranged_categories

def find_category_by_siedl(numer_siedl, ranged_categories):
    """
    Znajduje kategorię na podstawie numeru "Siedl" w zdefiniowanych zakresach.
    Zwraca słownik z danymi kategorii lub None, jeśli nie znaleziono.
    """
    try:
        num = int(numer_siedl)
        for cat in ranged_categories:
            if cat['start'] <= num <= cat['end']:
                return cat
    except (ValueError, TypeError):
        return None
    return None

def update_categories_and_create_new_file():
    """Główna funkcja skryptu: wczytuje, przetwarza i zapisuje dane do nowego pliku."""
    
    # Sprawdzenie, czy pliki wejściowe istnieją
    for filename in [PIESNI_INPUT_FILENAME, KATEGORIE_FILENAME]:
        if not os.path.exists(filename):
            print(f"BŁĄD: Plik wejściowy '{filename}' nie został znaleziony. Przerwanie działania.")
            return

    print(f"Wczytywanie danych z '{PIESNI_INPUT_FILENAME}' i '{KATEGORIE_FILENAME}'...")

    try:
        with open(KATEGORIE_FILENAME, 'r', encoding=FILE_ENCODING) as f:
            kategorie_content = f.read()
        with open(PIESNI_INPUT_FILENAME, 'r', encoding=FILE_ENCODING) as f:
            piesni_data = json.load(f)
    except json.JSONDecodeError:
        print(f"BŁĄD: Plik '{PIESNI_INPUT_FILENAME}' zawiera błędy w formacie JSON.")
        return
    except Exception as e:
        print(f"BŁĄD: Wystąpił problem podczas wczytywania plików: {e}")
        return

    # Przetworzenie pliku z kategoriami
    ranged_categories = parse_ranged_kategorie(kategorie_content)
    if not ranged_categories:
        print("OSTRZEŻENIE: Nie znaleziono kategorii z zakresem numerów w pliku 'Kategorie.txt'.")
    
    print("Rozpoczynam aktualizację kategorii dla pieśni...")
    
    updated_count = 0
    # Iteracja przez każdą pieśń w załadowanych danych
    for song_object in piesni_data:
        numer_siedl = song_object.get('numerSiedl')
        
        # Sprawdzenie, czy pole 'numerSiedl' istnieje i nie jest puste
        if numer_siedl:
            category_info = find_category_by_siedl(numer_siedl, ranged_categories)
            
            if category_info:
                song_object['kategoria'] = category_info['name']
                song_object['kategoriaSkr'] = category_info['abbr']
                updated_count += 1

    print(f"Zakończono przetwarzanie. Zaktualizowano kategorie dla {updated_count} pieśni.")
    print(f"Zapisywanie wyniku do nowego pliku: '{PIESNI_OUTPUT_FILENAME}'...")
    
    try:
        # Zapisanie zmodyfikowanej struktury danych do nowego pliku wyjściowego
        with open(PIESNI_OUTPUT_FILENAME, 'w', encoding=FILE_ENCODING) as f:
            json.dump(piesni_data, f, indent=JSON_INDENTATION, ensure_ascii=False)
        print(f"Operacja zakończona pomyślnie! Utworzono plik '{PIESNI_OUTPUT_FILENAME}'. Plik '{PIESNI_INPUT_FILENAME}' pozostał niezmieniony.")
    except Exception as e:
        print(f"BŁĄD: Wystąpił problem podczas zapisywania pliku wyjściowego: {e}")

# Uruchomienie głównej funkcji skryptu
if __name__ == "__main__":
    update_categories_and_create_new_file()