import os
import json
from typing import Dict, List, Any, Optional, Set

# --- Konfiguracja ---
LEKCJONARZ_DIR_NAME = '../Lekcjonarz_JSON2'
PIESNI_SOURCE_FILE_NAME = 'piesni.json'
OUTPUT_REPORT_FILE_NAME = 'raport_niespojnosci.json'

# Zbiór niedozwolonych tytułów pieśni dla szybkiego sprawdzania
DISALLOWED_TITLES: Set[str] = {
    "Ciebie, Boga, wysławiamy",
    "Przybądź, Duchu Święty, ześlij z nieba",
    "O Stworzycielu, Duchu",
    "Ciebie, Boże, chwalimy"
}

def load_master_songs(filepath: str) -> Optional[Dict[str, str]]:
    """
    Wczytuje główny plik z pieśniami i tworzy słownik do szybkiego wyszukiwania.

    Args:
        filepath: Ścieżka do pliku piesni.json.

    Returns:
        Słownik, w którym kluczem jest numer pieśni, a wartością jej tytuł.
        Zwraca None, jeśli plik nie zostanie znaleziony lub wystąpi błąd.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            songs_data = json.load(f)
            master_songs = {
                song.get('numer'): song.get('tytul')
                for song in songs_data if song.get('numer')
            }
            print(f"Pomyślnie wczytano {len(master_songs)} pieśni z pliku źródłowego '{filepath}'.")
            return master_songs
    except FileNotFoundError:
        print(f"BŁĄD: Nie znaleziono pliku źródłowego z pieśniami: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"BŁĄD: Plik {filepath} ma nieprawidłowy format JSON.")
        return None
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas wczytywania pieśni: {e}")
        return None

def verify_and_report_files(leksjonarz_path: str, master_songs: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Przechodzi przez pliki JSON w folderze lekcjonarza, weryfikuje pieśni
    i tworzy raport zawierający tylko pliki z błędami.

    Args:
        leksjonarz_path: Ścieżka do głównego folderu 'Lekcjonarz_JSON2'.
        master_songs: Słownik z pieśniami wczytanymi z pliku źródłowego.

    Returns:
        Lista słowników, gdzie każdy słownik reprezentuje plik z błędami.
    """
    problematic_files_report = []
    base_dir_abs = os.path.abspath(leksjonarz_path)

    if not os.path.isdir(base_dir_abs):
        print(f"BŁĄD: Folder {base_dir_abs} nie istnieje.")
        return problematic_files_report

    print(f"\nRozpoczynam weryfikację plików w: {base_dir_abs}")
    files_processed_count = 0

    for root, _, files in os.walk(base_dir_abs):
        for filename in files:
            if filename.endswith('.json'):
                files_processed_count += 1
                file_path = os.path.join(root, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        daily_data = json.load(f)
                except (json.JSONDecodeError, Exception) as e:
                    print(f"Ostrzeżenie: Pomijam plik z powodu błędu odczytu: {file_path}. Błąd: {e}")
                    continue

                suggested_songs = daily_data.get('piesniSugerowane', [])
                if not isinstance(suggested_songs, list):
                    continue
                
                errors_in_file_count = 0
                for song in suggested_songs:
                    song_number = song.get('numer')
                    song_title_in_day_file = song.get('piesn')

                    # Jeśli brakuje tytułu, nie możemy go sprawdzić
                    if not song_title_in_day_file:
                        continue

                    master_title = master_songs.get(song_number)

                    # Sprawdzanie niespójności:
                    # 1. Numer pieśni nie istnieje w pliku źródłowym.
                    # 2. Tytuł pieśni nie zgadza się z tytułem w pliku źródłowym.
                    is_mismatched = master_title is None or master_title != song_title_in_day_file
                    
                    # 3. Tytuł pieśni jest na liście niedozwolonych.
                    is_disallowed = song_title_in_day_file in DISALLOWED_TITLES

                    if is_mismatched or is_disallowed:
                        errors_in_file_count += 1
                
                if errors_in_file_count > 0:
                    relative_path = os.path.relpath(file_path, os.path.dirname(base_dir_abs))
                    
                    problematic_files_report.append({
                        'sciezka_pliku': relative_path.replace('\\', '/'),
                        'liczba_bledow': errors_in_file_count
                    })

    print(f"\nZakończono weryfikację. Sprawdzono łącznie {files_processed_count} plików .json.")
    return problematic_files_report

def save_report(report_data: List[Dict[str, Any]], output_filepath: str):
    """
    Zapisuje wyniki weryfikacji do pliku JSON.
    """
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4, ensure_ascii=False)
        
        if report_data:
            print(f"\nZnaleziono {len(report_data)} plików zawierających niespójności.")
            print(f"Szczegółowy raport został zapisany w pliku: {output_filepath}")
        else:
            print("\nWeryfikacja zakończona pomyślnie. Nie znaleziono żadnych niespójności w plikach.")
    except Exception as e:
        print(f"BŁĄD: Nie udało się zapisać pliku raportu. Błąd: {e}")

def main():
    """Główna funkcja sterująca wykonaniem skryptu."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    leksjonarz_path = os.path.join(script_dir, LEKCJONARZ_DIR_NAME)
    piesni_source_path = os.path.join(script_dir, PIESNI_SOURCE_FILE_NAME)
    report_output_path = os.path.join(script_dir, OUTPUT_REPORT_FILE_NAME)

    master_songs = load_master_songs(piesni_source_path)
    
    if master_songs is None:
        return

    report = verify_and_report_files(leksjonarz_path, master_songs)
    save_report(report, report_output_path)


if __name__ == '__main__':
    main()