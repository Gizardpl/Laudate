import os
import json
from collections import Counter, OrderedDict
from typing import Dict, List, Set

# Skrypt sprawdza, czy dla kluczowych momentów liturgicznych nie występuje tylko jedna propozycja pieśni.
# Jeśli tak, uznaje plik za błędny i kopiuje go do folderu 'zle', grupując w podfolderach po 30 plików.

# --- Konfiguracja ---
LEKCJONARZ_DIR_NAME = '../NiesprawdzoneDni'
BAD_FILES_DIR_NAME = 'zle'
FILES_PER_SUBFOLDER = 30  # Maksymalna liczba plików w jednym podfolderze

# Moment, dla których liczba pieśni równa 1 jest uznawana za błąd.
MOMENTS_TO_CHECK_FOR_SINGULARITY: Set[str] = {
    "wejscie",
    "ofiarowanie",
    "komunia",
    "uwielbienie",
    "rozeslanie"
}

def copy_bad_file(source_path: str, destination_dir: str, base_dir: str):
    """
    Kopiuje plik uznany za błędny do folderu docelowego,
    dodając na początku jego treści klucz 'sciezka' z względną ścieżką do oryginału.

    Args:
        source_path: Pełna ścieżka do oryginalnego, błędnego pliku.
        destination_dir: Ścieżka do folderu, gdzie plik ma być skopiowany.
        base_dir: Główny katalog, względem którego obliczana jest ścieżka względna.
    """
    try:
        relative_path = os.path.relpath(source_path, os.path.dirname(base_dir)).replace('\\', '/')
        
        with open(source_path, 'r', encoding='utf-8') as f_in:
            file_data = json.load(f_in, object_pairs_hook=OrderedDict)

        new_data = OrderedDict()
        new_data['sciezka'] = relative_path
        new_data.update(file_data)

        file_name = os.path.basename(source_path)
        destination_file_path = os.path.join(destination_dir, file_name)

        with open(destination_file_path, 'w', encoding='utf-8') as f_out:
            json.dump(new_data, f_out, indent=2, ensure_ascii=False)
        
        print(f"  -> Skopiowano: {relative_path} do folderu '{os.path.basename(os.path.dirname(destination_file_path))}/{os.path.basename(destination_file_path)}'")

    except Exception as e:
        print(f"BŁĄD podczas kopiowania pliku '{source_path}': {e}")


def verify_and_identify_bad_files(leksjonarz_path: str) -> List[str]:
    """
    Przechodzi przez pliki JSON i identyfikuje te, które dla kluczowych momentów
    zawierają dokładnie jedną pieśń.

    Args:
        leksjonarz_path: Ścieżka do głównego folderu 'Lekcjonarz_JSON2'.

    Returns:
        Lista pełnych ścieżek do plików, które zawierają błędy.
    """
    problematic_files = []
    base_dir_abs = os.path.abspath(leksjonarz_path)

    if not os.path.isdir(base_dir_abs):
        print(f"BŁĄD: Folder {base_dir_abs} nie istnieje.")
        return problematic_files

    print(f"\nRozpoczynam weryfikację plików w: {base_dir_abs}")
    files_processed_count = 0

    for root, _, files in os.walk(base_dir_abs):
        for filename in files:
            if filename.endswith('.json'):
                files_processed_count += 1
                file_path = os.path.join(root, filename)
                is_bad_file = False
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        daily_data = json.load(f)
                except (json.JSONDecodeError, Exception) as e:
                    print(f"Ostrzeżenie: Pomijam plik z powodu błędu odczytu: {file_path}. Błąd: {e}")
                    problematic_files.append(file_path)
                    continue

                suggested_songs = daily_data.get('piesniSugerowane', [])
                if not isinstance(suggested_songs, list):
                    continue

                # Zlicz wystąpienia każdego 'momentu' w pliku
                moment_counts = Counter(s.get('moment') for s in suggested_songs if s.get('moment'))
                
                # Sprawdź, czy dla któregokolwiek z kluczowych momentów liczba pieśni wynosi 1
                for moment in MOMENTS_TO_CHECK_FOR_SINGULARITY:
                    if moment_counts.get(moment) == 1:
                        is_bad_file = True
                        break  # Wystarczy jeden taki przypadek, by uznać plik za zły
                
                if is_bad_file:
                    problematic_files.append(file_path)

    print(f"\nZakończono weryfikację. Sprawdzono łącznie {files_processed_count} plików .json.")
    return problematic_files

def main():
    """Główna funkcja sterująca wykonaniem skryptu."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    leksjonarz_path = os.path.join(script_dir, LEKCJONARZ_DIR_NAME)
    bad_files_base_path = os.path.join(script_dir, BAD_FILES_DIR_NAME)

    os.makedirs(bad_files_base_path, exist_ok=True)
    print(f"Główny folder na błędne pliki '{bad_files_base_path}' jest gotowy.")

    bad_files_list = verify_and_identify_bad_files(leksjonarz_path)

    if bad_files_list:
        print(f"\nZnaleziono {len(bad_files_list)} plików z błędami. Rozpoczynam kopiowanie i grupowanie...")
        
        for i, file_path in enumerate(bad_files_list):
            # Oblicz numer podfolderu (zaczynając od 1)
            subfolder_number = (i // FILES_PER_SUBFOLDER) + 1
            subfolder_path = os.path.join(bad_files_base_path, str(subfolder_number))

            # Utwórz podfolder, jeśli jeszcze nie istnieje
            os.makedirs(subfolder_path, exist_ok=True)

            # Skopiuj plik do odpowiedniego podfolderu
            copy_bad_file(file_path, subfolder_path, leksjonarz_path)
            
        print("\nZakończono kopiowanie wszystkich zidentyfikowanych plików.")
    else:
        print("\nWeryfikacja zakończona pomyślnie. Nie znaleziono żadnych plików z błędami.")


if __name__ == '__main__':
    main()