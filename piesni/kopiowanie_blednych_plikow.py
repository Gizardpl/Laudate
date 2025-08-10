import os
import json
from collections import OrderedDict

# --- Konfiguracja ---
# Nazwa pliku z raportem o niespójnościach
REPORT_FILE_NAME = 'raport_niespojnosci.json'

# Nazwa folderu, w którym zostaną umieszczone kopie plików do poprawy
OUTPUT_DIR_NAME = 'Poprawa'

# Ścieżka bazowa, gdzie znajduje się główny folder z lekcjonarzem
# '../' oznacza jeden folder w górę od lokalizacji skryptu
SOURCE_BASE_DIR = '../'

# Maksymalna liczba plików w jednym podfolderze
BATCH_SIZE = 20


def organize_files_into_batches(report_path: str, output_dir_path: str):
    """
    Wczytuje plik raportu i kopiuje wskazane pliki do folderu wyjściowego,
    grupując je w ponumerowanych podfolderach.

    Args:
        report_path: Ścieżka do pliku raportu JSON.
        output_dir_path: Ścieżka do folderu, gdzie będą zapisywane kopie.
    """
    # 1. Wczytaj plik raportu
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        print(f"Pomyślnie wczytano raport z pliku: '{report_path}'.")
    except FileNotFoundError:
        print(f"BŁĄD: Nie można znaleźć pliku raportu: '{report_path}'. Upewnij się, że plik istnieje.")
        return
    except json.JSONDecodeError:
        print(f"BŁĄD: Plik raportu '{report_path}' ma nieprawidłowy format JSON.")
        return
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas odczytu raportu: {e}")
        return

    # 2. Utwórz główny folder wyjściowy, jeśli nie istnieje
    os.makedirs(output_dir_path, exist_ok=True)
    print(f"Główny folder wyjściowy '{output_dir_path}' jest gotowy.")

    copied_files_count = 0
    
    # 3. Przetwórz każdy wpis w raporcie, wykonując tylko jedną operację kopiowania
    for i, item in enumerate(report_data):
        # Określ numer podfolderu dla bieżącego pliku
        batch_folder_index = (i // BATCH_SIZE) + 1
        current_batch_dir = os.path.join(output_dir_path, str(batch_folder_index))
        
        # Utwórz podfolder dla bieżącej partii plików, jeśli jeszcze nie istnieje
        os.makedirs(current_batch_dir, exist_ok=True)

        relative_path = item.get("sciezka_pliku")
        if not relative_path:
            print("Ostrzeżenie: Pomijam wpis w raporcie bez klucza 'sciezka_pliku'.")
            continue

        # Zbuduj pełną ścieżkę do pliku źródłowego i docelowego
        source_file_path = os.path.join(SOURCE_BASE_DIR, relative_path)
        dest_file_name = os.path.basename(source_file_path)
        dest_file_path = os.path.join(current_batch_dir, dest_file_name)

        try:
            # Wczytaj oryginalny plik JSON, zachowując kolejność
            with open(source_file_path, 'r', encoding='utf-8') as f:
                original_data = json.load(f, object_pairs_hook=OrderedDict)

            # Przygotuj nowe dane z komentarzem na początku
            new_data = OrderedDict()
            new_data["__KOMENTARZ_SCIEZKA_ZRODLOWA__"] = relative_path.replace('\\', '/')
            new_data.update(original_data)

            # Zapisz plik w odpowiednim podfolderze
            with open(dest_file_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)
            
            copied_files_count += 1
            print(f"Skopiowano: '{relative_path}' -> '{dest_file_path}'")

        except FileNotFoundError:
            print(f"Ostrzeżenie: Nie znaleziono pliku źródłowego: '{source_file_path}'. Pomijam.")
        except Exception as e:
            print(f"BŁĄD podczas przetwarzania pliku '{source_file_path}': {e}")
            
    print(f"\nZakończono. Skopiowano i pogrupowano łącznie {copied_files_count} z {len(report_data)} plików z raportu.")


def main():
    """Główna funkcja sterująca wykonaniem skryptu."""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_file_path = os.path.join(script_dir, REPORT_FILE_NAME)
    output_dir_path = os.path.join(script_dir, OUTPUT_DIR_NAME)

    organize_files_into_batches(report_file_path, output_dir_path)


if __name__ == '__main__':
    main()