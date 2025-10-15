import json
import os
import re
from collections import OrderedDict

# ==============================================================================
# KONFIGURACJA
# Zdefiniuj nazwy plików oraz parametry, które będą używane w skrypcie.
# ==============================================================================

# Plik JSON zawierający nowe pieśni do dodania lub zaktualizowania.
NEW_SONGS_FILENAME = 'ED.json'

# Plik JSON z główną bazą pieśni, który będzie celem operacji.
MAIN_SONGS_INPUT_FILENAME = 'piesni1.json'

# Nazwa pliku wyjściowego, który zostanie utworzony z połączonymi danymi.
MAIN_SONGS_OUTPUT_FILENAME = 'piesni2.json'

# Nazwa klucza (parametru) oznaczającego tytuł pieśni w OBU plikach.
TITLE_PARAM_NAME = 'tytul'

# Nazwa klucza (parametru) oznaczającego numer pieśni w pliku z NOWYMI pieśniami.
# Skrypt wyszuka tego samego klucza w pliku głównym.
NUMBER_PARAM_NAME = 'numerED'

# Kodowanie znaków używane do odczytu i zapisu plików.
FILE_ENCODING = 'utf-8'

# Wcięcie dla wynikowego pliku JSON (dla lepszej czytelności).
JSON_INDENTATION = 4

# Ustaw na True, aby wyświetlać w konsoli informację o każdej porównywanej pieśni.
# Ustaw na False, aby widzieć tylko podsumowanie.
VERBOSE_LOGGING = True

# ==============================================================================
# FUNKCJE POMOCNICZE
# ==============================================================================

def normalize_title(title):
    """
    Normalizuje tytuł pieśni do ujednoliconej formy w celu porównania.
    Kroki:
    1. Zmienia wszystkie litery na małe.
    2. Usuwa wszystkie znaki, które nie są literami ani cyframi (poza polskimi znakami).
    3. Dzieli tekst na słowa.
    4. Sortuje słowa alfabetycznie.
    5. Łączy posortowane słowa w jeden ciąg znaków.
    """
    if not title:
        return ""
    # Zastąp polskie znaki ich podstawowymi odpowiednikami dla spójnego sortowania
    title = title.lower()
    replacements = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'}
    for pl, en in replacements.items():
        title = title.replace(pl, en)

    cleaned_title = re.sub(r'[\W\s_]+', ' ', title).strip()
    words = sorted(cleaned_title.split())
    return "".join(words)

def validate_structure(song_list, filename):
    """
    Sprawdza, czy wszystkie obiekty w liście mają identyczną strukturę.
    Zwraca listę kluczy (strukturę) jeśli jest spójna, w przeciwnym razie None.
    """
    if not song_list:
        print(f"OSTRZEŻENIE: Plik '{filename}' jest pusty. Nie można ustalić struktury.")
        return None

    base_structure = list(song_list[0].keys())
    print(f"Ustalono bazową strukturę na podstawie pierwszej pieśni z '{filename}': {base_structure}")

    for i, song in enumerate(song_list[1:], start=1):
        current_structure = list(song.keys())
        if current_structure != base_structure:
            print("\n" + "="*80)
            print(f"BŁĄD KRYTYCZNY: Niespójna struktura w pliku '{filename}'.")
            print(f"Pieśń nr {i+1} (tytuł: '{song.get(TITLE_PARAM_NAME, 'Brak tytułu')}') ma inną strukturę.")
            print(f"Struktura oczekiwana (z pierwszej pieśni): {base_structure}")
            print(f"Struktura znaleziona (w tej pieśni):   {current_structure}")
            print("Przerwanie działania. Popraw plik, aby wszystkie obiekty miały tę samą kolejność i zestaw parametrów.")
            print("="*80 + "\n")
            return None
    
    print(f"Struktura w pliku '{filename}' jest spójna. Można kontynuować.")
    return base_structure

# ==============================================================================
# GŁÓWNA FUNKCJA SKRYPTU
# ==============================================================================

def process_song_files():
    """
    Główna funkcja skryptu: weryfikuje, porównuje, aktualizuje i dodaje pieśni.
    """
    
    # --- Krok 1: Sprawdzenie, czy pliki wejściowe istnieją ---
    for filename in [NEW_SONGS_FILENAME, MAIN_SONGS_INPUT_FILENAME]:
        if not os.path.exists(filename):
            print(f"BŁĄD KRYTYCZNY: Plik wejściowy '{filename}' nie został znaleziony. Przerwanie działania.")
            return

    print("Rozpoczynam proces aktualizacji bazy pieśni...")

    # --- Krok 2: Wczytanie danych z plików JSON ---
    try:
        with open(NEW_SONGS_FILENAME, 'r', encoding=FILE_ENCODING) as f:
            new_songs_data = json.load(f)
        with open(MAIN_SONGS_INPUT_FILENAME, 'r', encoding=FILE_ENCODING) as f:
            main_songs_data = json.load(f)
        print(f"Pomyślnie wczytano {len(new_songs_data)} pieśni z '{NEW_SONGS_FILENAME}'.")
        print(f"Pomyślnie wczytano {len(main_songs_data)} pieśni z '{MAIN_SONGS_INPUT_FILENAME}'.\n")
    except json.JSONDecodeError as e:
        print(f"BŁĄD KRYTYCZNY: Wystąpił błąd formatu w jednym z plików JSON. Szczegóły: {e}")
        return
    except Exception as e:
        print(f"BŁĄD KRYTYCZNY: Wystąpił problem podczas wczytywania plików: {e}")
        return

    # --- Krok 3: Weryfikacja struktury głównego pliku pieśni ---
    base_structure = validate_structure(main_songs_data, MAIN_SONGS_INPUT_FILENAME)
    if base_structure is None:
        return

    # --- Krok 4: Stworzenie mapy znormalizowanych tytułów dla optymalizacji ---
    main_songs_map = {normalize_title(song.get(TITLE_PARAM_NAME, '')): song for song in main_songs_data}
    
    updated_count = 0
    added_count = 0
    structure_mismatch_logs = []

    # --- Krok 5: Iteracja przez nowe pieśni i ich przetwarzanie ---
    print("\nRozpoczynam porównywanie i scalanie danych...")
    for new_song in new_songs_data:
        title = new_song.get(TITLE_PARAM_NAME, '').strip()
        if not title:
            continue

        normalized_new_title = normalize_title(title)
        
        if normalized_new_title in main_songs_map:
            # AKTUALIZACJA ISTNIEJĄCEJ PIEŚNI
            existing_song = main_songs_map[normalized_new_title]
            new_number = new_song.get(NUMBER_PARAM_NAME, '')
            
            if VERBOSE_LOGGING:
                print(f"INFO: Pieśń '{title}' ma duplikat w bazie: '{existing_song[TITLE_PARAM_NAME]}'.")
            
            if new_number:
                if NUMBER_PARAM_NAME in existing_song:
                    existing_song[NUMBER_PARAM_NAME] = new_number
                    updated_count += 1
                    if VERBOSE_LOGGING:
                        print(f"      -> Zaktualizowano numer '{NUMBER_PARAM_NAME}' na: '{new_number}'.")
                else:
                    log_msg = (f"NIEZGODNOŚĆ STRUKTURY: Próba aktualizacji parametru '{NUMBER_PARAM_NAME}' "
                               f"dla pieśni '{title}', ale taki parametr nie istnieje w pliku głównym.")
                    structure_mismatch_logs.append(log_msg)
        else:
            # DODAWANIE NOWEJ PIEŚNI
            if VERBOSE_LOGGING:
                print(f"INFO: Pieśń '{title}' nie ma duplikatu. Dodawanie nowego wpisu.")
            
            new_song_obj = OrderedDict((key, "") for key in base_structure)
            
            new_song_obj[TITLE_PARAM_NAME] = title
            
            new_number = new_song.get(NUMBER_PARAM_NAME, '')
            if new_number:
                if NUMBER_PARAM_NAME in new_song_obj:
                    new_song_obj[NUMBER_PARAM_NAME] = new_number
                else:
                    log_msg = (f"NIEZGODNOŚĆ STRUKTURY: Próba dodania numeru do parametru '{NUMBER_PARAM_NAME}' "
                               f"dla nowej pieśni '{title}', ale taki parametr nie istnieje w strukturze docelowej.")
                    structure_mismatch_logs.append(log_msg)
            
            new_entry = dict(new_song_obj)
            main_songs_data.append(new_entry)
            added_count += 1
            main_songs_map[normalized_new_title] = new_entry

    # --- Krok 6: Zapisanie wyniku i podsumowanie ---
    print("\n" + "="*80)
    print("Zakończono przetwarzanie. Podsumowanie:")
    print(f" - Zaktualizowano numer '{NUMBER_PARAM_NAME}' dla {updated_count} istniejących pieśni.")
    print(f" - Dodano {added_count} nowych pieśni do bazy.")
    
    if structure_mismatch_logs:
        print("\nUWAGA: Wystąpiły następujące niezgodności struktury parametrów:")
        for log in structure_mismatch_logs:
            print(f"  - {log}")

    try:
        with open(MAIN_SONGS_OUTPUT_FILENAME, 'w', encoding=FILE_ENCODING) as f:
            json.dump(main_songs_data, f, indent=JSON_INDENTATION, ensure_ascii=False)
        print(f"\nOperacja zakończona pomyślnie! Zaktualizowana baza została zapisana w pliku '{MAIN_SONGS_OUTPUT_FILENAME}'.")
    except Exception as e:
        print(f"BŁĄD KRYTYCZNY: Wystąpił problem podczas zapisywania pliku wyjściowego: {e}")
    print("="*80)

# ==============================================================================
# URUCHOMIENIE SKRYPTU
# ==============================================================================
if __name__ == "__main__":
    process_song_files()