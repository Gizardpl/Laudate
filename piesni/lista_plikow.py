import os
import json

# robi listę plików w folderze źródłowym i zapisuje ją do pliku .json

def stworz_liste_plikow_json(folder_zrodlowy: str, plik_docelowy: str):
    """
    Przeszukuje folder źródłowy w poszukiwaniu plików .json i tworzy
    plik .json zawierający listę ich nazw jako klucze.

    Args:
        folder_zrodlowy (str): Ścieżka do folderu, który ma być przeszukany.
        plik_docelowy (str): Nazwa pliku wyjściowego, który zostanie utworzony.
    """
    # Sprawdzenie, czy folder źródłowy istnieje
    if not os.path.isdir(folder_zrodlowy):
        print(f"BŁĄD: Folder '{folder_zrodlowy}' nie został znaleziony.")
        return

    # Słownik do przechowywania wyników (nazwa_pliku: "")
    wyniki = {}

    print(f"Przeszukiwanie folderu '{folder_zrodlowy}'...")

    # Przechodzenie przez wszystkie pliki i podfoldery
    for root, _, files in os.walk(folder_zrodlowy):
        for file in files:
            # Sprawdzanie, czy plik ma rozszerzenie .json
            if file.endswith('.json'):
                # Pobieranie nazwy pliku bez rozszerzenia
                nazwa_klucza = os.path.splitext(file)[0]
                # Dodawanie klucza z pustą wartością do słownika
                wyniki[nazwa_klucza] = ""

    # Sprawdzenie, czy znaleziono jakiekolwiek pliki
    if not wyniki:
        print("Nie znaleziono żadnych plików .json.")
        return

    # Zapisywanie słownika do pliku docelowego w formacie JSON
    try:
        with open(plik_docelowy, 'w', encoding='utf-8') as f:
            # Użycie indent=4 dla czytelności pliku i ensure_ascii=False dla polskich znaków
            json.dump(wyniki, f, indent=4, ensure_ascii=False)
        print(f"Pomyślnie utworzono plik '{plik_docelowy}' zawierający {len(wyniki)} pozycji.")
    except IOError as e:
        print(f"BŁĄD: Nie można zapisać pliku '{plik_docelowy}'. Powód: {e}")


def main():
    """Główna funkcja skryptu."""
    # Konfiguracja
    folder_do_przeszukania = '../NiesprawdzoneDni'
    nazwa_pliku_wynikowego = 'lista.json'
    
    # Wywołanie funkcji
    stworz_liste_plikow_json(folder_do_przeszukania, nazwa_pliku_wynikowego)


# Uruchomienie skryptu
if __name__ == '__main__':
    main()