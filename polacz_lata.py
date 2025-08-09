import os
import shutil
import re

def organize_liturgical_files(root_dir, skip_dir_name='Święta i Uroczystości'):
    """
    Organizuje pliki JSON z czytaniami liturgicznymi, grupując pliki
    dla różnych lat (A, B, C, I, II) w dedykowane foldery.

    Args:
        root_dir (str): Ścieżka do głównego katalogu (np. 'Lekcjonarz_JSON2').
        skip_dir_name (str): Nazwa katalogu do pominięcia w procesie.
    """
    if not os.path.isdir(root_dir):
        print(f"Błąd: Katalog '{root_dir}' nie został znaleziony.")
        return

    print(f"Rozpoczynam organizację plików w '{root_dir}'...")
    print(f"Katalog '{skip_dir_name}' zostanie pominięty.\n")

    moved_files_count = 0
    created_dirs_count = 0
    
    # Wyrażenie regularne do znalezienia plików z rokiem i wyodrębnienia nazwy bazowej
    # np. z "Nazwa pliku rok A.json" wychwyci "Nazwa pliku" oraz " rok A"
    pattern = re.compile(r"^(.*?)( rok [ABCII]+)\.json$")

    # os.walk pozwala na rekursywne przeglądanie katalogów
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Pomijanie wskazanego katalogu przez usunięcie go z listy do odwiedzenia
        if skip_dir_name in dirnames:
            print(f"Pomijam katalog: {os.path.join(dirpath, skip_dir_name)}")
            dirnames.remove(skip_dir_name)

        for filename in filenames:
            match = pattern.match(filename)
            
            # Jeśli nazwa pliku pasuje do naszego wzorca
            if match:
                base_name = match.group(1).strip()
                
                # Ścieżka do oryginalnego pliku
                old_path = os.path.join(dirpath, filename)
                
                # Tworzenie ścieżki do nowego folderu
                new_folder_path = os.path.join(dirpath, base_name)
                
                # Tworzenie folderu, jeśli jeszcze nie istnieje
                if not os.path.exists(new_folder_path):
                    try:
                        os.makedirs(new_folder_path)
                        print(f"-> Utworzono folder: {new_folder_path}")
                        created_dirs_count += 1
                    except OSError as e:
                        print(f"Błąd podczas tworzenia folderu {new_folder_path}: {e}")
                        continue

                # Przenoszenie pliku do nowego folderu
                try:
                    new_file_path = os.path.join(new_folder_path, filename)
                    shutil.move(old_path, new_file_path)
                    print(f"   Przeniesiono: {filename} -> {new_folder_path}/")
                    moved_files_count += 1
                except Exception as e:
                    print(f"Błąd podczas przenoszenia pliku {old_path}: {e}")

    print("\n--- Zakończono ---")
    print(f"Łącznie przeniesiono plików: {moved_files_count}")
    print(f"Łącznie utworzono nowych folderów: {created_dirs_count}")


# --- Uruchomienie skryptu ---
if __name__ == "__main__":
    # Upewnij się, że ten skrypt znajduje się w tym samym miejscu
    # co folder 'Lekcjonarz_JSON2', lub podaj pełną ścieżkę.
    main_directory = 'Lekcjonarz_JSON2'
    organize_liturgical_files(main_directory)