import os
import json

# --- Konfiguracja ---
# Nazwa pliku wejściowego zawierającego poprawione dane
INPUT_FILE_WITH_CORRECTIONS = 'poprawione.json'

# Ścieżka bazowa, gdzie znajduje się główny folder z lekcjonarzem
# '../' oznacza jeden folder w górę od lokalizacji skryptu
SOURCE_BASE_DIR = '../'


def apply_corrections(corrections_filepath: str):
    """
    Wczytuje plik z poprawkami i aktualizuje odpowiednie pliki docelowe,
    nadpisując w nich sekcję 'piesniSugerowane'.

    Args:
        corrections_filepath: Ścieżka do pliku JSON z poprawkami.
    """
    # 1. Wczytaj plik z poprawkami
    try:
        with open(corrections_filepath, 'r', encoding='utf-8') as f:
            corrections_data = json.load(f)
        print(f"Pomyślnie wczytano plik z poprawkami: '{corrections_filepath}'.")
    except FileNotFoundError:
        print(f"BŁĄD KRYTYCZNY: Nie można znaleźć pliku z poprawkami: '{corrections_filepath}'. Przerwanie operacji.")
        return
    except json.JSONDecodeError:
        print(f"BŁĄD KRYTYCZNY: Plik '{corrections_filepath}' ma nieprawidłowy format JSON. Przerwanie operacji.")
        return
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas odczytu pliku z poprawkami: {e}")
        return

    if not isinstance(corrections_data, list):
        print("BŁĄD KRYTYCZNY: Plik z poprawkami nie zawiera listy obiektów.")
        return

    updated_files_count = 0
    failed_files_count = 0
    
    # 2. Przetwórz każdy obiekt (każdą poprawkę) z pliku
    for item in corrections_data:
        relative_path = item.get("sciezka")
        new_songs_data = item.get("piesniSugerowane")

        if not relative_path or new_songs_data is None:
            print(f"Ostrzeżenie: Pomijam niekompletny wpis w pliku z poprawkami: {item}")
            failed_files_count += 1
            continue

        # Zbuduj pełną ścieżkę do pliku, który ma zostać zaktualizowany
        target_file_path = os.path.normpath(os.path.join(SOURCE_BASE_DIR, relative_path))

        try:
            # Wczytaj zawartość oryginalnego pliku
            with open(target_file_path, 'r', encoding='utf-8') as f:
                original_file_data = json.load(f)

            # Podmień sekcję z pieśniami na nową, poprawioną wersję
            original_file_data['piesniSugerowane'] = new_songs_data

            # Zapisz (nadpisz) plik z powrotem z nowymi danymi
            with open(target_file_path, 'w', encoding='utf-8') as f:
                json.dump(original_file_data, f, indent=2, ensure_ascii=False)
            
            updated_files_count += 1
            print(f"OK: Zaktualizowano plik '{target_file_path}'")

        except FileNotFoundError:
            print(f"BŁĄD: Nie znaleziono pliku docelowego: '{target_file_path}'. Pomijam.")
            failed_files_count += 1
        except KeyError:
            print(f"BŁĄD: W pliku '{target_file_path}' brakuje klucza 'piesniSugerowane'. Nie można dokonać podmiany.")
            failed_files_count += 1
        except Exception as e:
            print(f"BŁĄD podczas przetwarzania pliku '{target_file_path}': {e}")
            failed_files_count += 1
            
    print("\n--- Podsumowanie ---")
    print(f"Pomyślnie zaktualizowano: {updated_files_count} plików.")
    if failed_files_count > 0:
        print(f"Nie udało się przetworzyć: {failed_files_count} plików (sprawdź komunikaty BŁĘDÓW/OSTRZEŻEŃ powyżej).")
    print("Operacja zakończona.")


def main():
    """Główna funkcja sterująca wykonaniem skryptu."""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    corrections_file_path = os.path.join(script_dir, INPUT_FILE_WITH_CORRECTIONS)

    apply_corrections(corrections_file_path)


if __name__ == '__main__':
    main()