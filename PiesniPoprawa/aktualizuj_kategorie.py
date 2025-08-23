import json
import re
import os

def parse_categories(file_path):
    """
    Parsuje plik Kategorie.txt, aby wyodrębnić zakresy numerów i odpowiadające im kategorie.

    Args:
        file_path (str): Ścieżka do pliku Kategorie.txt.

    Returns:
        list: Lista krotek, gdzie każda krotka zawiera (start_num, end_num, category, category_short).
    """
    categories = []
    # Wyrażenie regularne do dopasowania linii z zakresem numerów, nazwą kategorii i skrótem
    pattern = re.compile(r'(\d+)\s*-\s*(\d+)\s*-\s*([^\{]+)\s*\{([^\}]+)\}')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    start, end, cat, cat_short = match.groups()
                    categories.append((int(start), int(end), cat.strip(), cat_short.strip()))
    except FileNotFoundError:
        print(f"Błąd: Plik '{file_path}' nie został znaleziony.")
        return None
    return categories

def find_category(song_number, categories):
    """
    Znajduje kategorię dla danego numeru pieśni na podstawie listy kategorii.

    Args:
        song_number (int): Numer pieśni do sklasyfikowania.
        categories (list): Lista kategorii sparsowana z pliku.

    Returns:
        tuple: Krotka (category, category_short) lub (None, None), jeśli nie znaleziono dopasowania.
    """
    for start, end, cat, cat_short in categories:
        if start <= song_number <= end:
            return cat, cat_short
    return None, None

def update_songs_categories(input_json_path, categories_txt_path, output_json_path):
    """
    Czyta plik JSON z pieśniami, aktualizuje puste kategorie na podstawie numeru Siedleckiego
    i zapisuje wyniki do nowego pliku JSON.
    """
    categories_map = parse_categories(categories_txt_path)
    if categories_map is None:
        return

    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            songs = json.load(f)
    except FileNotFoundError:
        print(f"Błąd: Plik wejściowy '{input_json_path}' nie został znaleziony.")
        return
    except json.JSONDecodeError:
        print(f"Błąd: Plik '{input_json_path}' nie jest prawidłowym plikiem JSON.")
        return
        
    updated_songs = []
    uncategorized_count = 0

    for song in songs:
        # Sprawdzamy, czy kategoria jest pusta i czy numerSiedl istnieje i nie jest pusty
        if not song.get('kategoria') and song.get('numerSiedl'):
            try:
                song_number = int(song['numerSiedl'])
                category, category_short = find_category(song_number, categories_map)
                
                if category and category_short:
                    song['kategoria'] = category
                    song['kategoriaSkr'] = category_short
                    print(f"Zaktualizowano pieśń nr {song_number} ('{song['tytul']}'): Kategoria -> {category}")
                else:
                    # Jeśli nie znaleziono kategorii, pozostawiamy puste i informujemy
                    uncategorized_count += 1
                    print(f"Ostrzeżenie: Nie znaleziono kategorii dla pieśni nr {song_number} ('{song['tytul']}'). Pozostawiono bez zmian.")

            except (ValueError, TypeError):
                # Obsługa przypadku, gdy numerSiedl nie jest liczbą
                uncategorized_count += 1
                print(f"Ostrzeżenie: Nieprawidłowy numerSiedl ('{song['numerSiedl']}') dla pieśni '{song['tytul']}'.")

        updated_songs.append(song)
        
    # Zapisywanie zaktualizowanej listy do nowego pliku JSON
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(updated_songs, f, ensure_ascii=False, indent=4)
        print(f"\nPrzetwarzanie zakończone. Zaktualizowane dane zostały zapisane w pliku '{output_json_path}'.")
        if uncategorized_count > 0:
            print(f"Liczba pieśni, dla których nie udało się ustalić kategorii: {uncategorized_count}.")
    except IOError as e:
        print(f"Błąd podczas zapisywania pliku '{output_json_path}': {e}")


# --- Uruchomienie skryptu ---
# Upewnij się, że pliki 'piesni5.json' i 'Kategorie.txt' znajdują się w tym samym folderze co skrypt,
# lub podaj pełne ścieżki do tych plików.

input_file = 'piesni5.json'
categories_file = 'Kategorie.txt'
output_file = 'piesni1.json'

# Sprawdzenie, czy pliki wejściowe istnieją
if os.path.exists(input_file) and os.path.exists(categories_file):
    update_songs_categories(input_file, categories_file, output_file)
else:
    print("Błąd: Upewnij się, że pliki 'piesni5.json' i 'Kategorie.txt' znajdują się w bieżącym folderze.")