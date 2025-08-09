import os
import json

def sanitize_filename(name):
    """
    Usuwa znaki, które są niedozwolone w nazwach plików w niektórych systemach operacyjnych.
    """
    invalid_chars = r'<>:"/\|?*'
    sanitized_name = "".join(c for c in name if c not in invalid_chars)
    # Usuwa białe znaki z początku i końca nazwy
    sanitized_name = sanitized_name.strip()
    return sanitized_name

def rename_json_files_by_title(root_dir):
    """
    Przechodzi przez podany katalog, odczytuje pliki JSON i zmienia ich nazwy
    na podstawie wartości klucza 'tytul_dnia'.
    """
    if not os.path.isdir(root_dir):
        print(f"Błąd: Katalog '{root_dir}' nie został znaleziony.")
        return

    print(f"Rozpoczynam przetwarzanie plików w katalogu: {root_dir}\n")
    renamed_count = 0
    skipped_count = 0

    # os.walk przechodzi przez wszystkie pliki i foldery wewnątrz root_dir
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.json'):
                old_path = os.path.join(dirpath, filename)
                
                try:
                    # Otwieramy plik z kodowaniem UTF-8 na wypadek polskich znaków
                    with open(old_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Sprawdzamy, czy klucz 'tytul_dnia' istnieje w pliku
                    if 'tytul_dnia' not in data or not data['tytul_dnia']:
                        print(f"Pominięto (brak tytułu): {old_path}")
                        skipped_count += 1
                        continue
                        
                    # Tworzymy nową nazwę pliku
                    new_name_base = sanitize_filename(data['tytul_dnia'])
                    new_filename = f"{new_name_base}.json"
                    new_path = os.path.join(dirpath, new_filename)

                    # Zmieniamy nazwę tylko, jeśli nowa nazwa jest inna od starej
                    if old_path != new_path:
                        # Sprawdzamy, czy plik o nowej nazwie już nie istnieje
                        if os.path.exists(new_path):
                            print(f"Pominięto (plik docelowy istnieje): {filename} -> {new_filename}")
                            skipped_count += 1
                        else:
                            os.rename(old_path, new_path)
                            print(f"Zmieniono nazwę: {filename} -> {new_filename}")
                            renamed_count += 1

                except json.JSONDecodeError:
                    print(f"Pominięto (błąd formatu JSON): {old_path}")
                    skipped_count += 1
                except Exception as e:
                    print(f"Pominięto (nieoczekiwany błąd: {e}): {old_path}")
                    skipped_count += 1
    
    print("\n--- Podsumowanie ---")
    print(f"Pomyślnie zmieniono nazwę {renamed_count} plików.")
    print(f"Pominięto {skipped_count} plików.")


# --- Uruchomienie skryptu ---
if __name__ == "__main__":
    # Upewnij się, że skrypt jest uruchamiany w tym samym katalogu,
    # w którym znajduje się folder 'Lekcjonarz_JSON2'
    # lub podaj pełną ścieżkę do tego folderu.
    root_directory = 'Lekcjonarz_JSON2'
    rename_json_files_by_title(root_directory)