import os
import json
from collections import OrderedDict

# Kopiuje pliki z folderu i grupuje gdzie indziej w podfolderach po X plików (dopisuje też ścieżkę względną)

# --- Konfiguracja ---
# Nazwa folderu źródłowego (o jeden poziom wyżej niż skrypt)
FOLDER_ZRODLOWY = '../Lekcjonarz_JSON2'

# Nazwa folderu docelowego, który zostanie utworzony
FOLDER_DOCELOWY = 'Kopia'

# Liczba plików, które mają znaleźć się w jednym podfolderze
PLIKOW_W_FOLDERZE = 40


def reorganizuj_i_kopiuj_pliki(zrodlo: str, cel: str, rozmiar_paczki: int):
    """
    Przeszukuje folder źródłowy, kopiuje wszystkie pliki .json do folderu
    docelowego, grupując je w podfolderach i dodając ścieżkę do ich treści.

    Args:
        zrodlo (str): Ścieżka do folderu źródłowego.
        cel (str): Ścieżka do folderu docelowego.
        rozmiar_paczki (int): Maksymalna liczba plików w jednym podfolderze.
    """
    # 1. Sprawdź, czy folder źródłowy istnieje
    if not os.path.isdir(zrodlo):
        print(f"BŁĄD: Folder źródłowy '{zrodlo}' nie został znaleziony. Upewnij się, że skrypt jest w odpowiednim miejscu.")
        return

    # 2. Zbierz listę wszystkich plików .json z folderu źródłowego
    wszystkie_pliki_json = []
    for root, _, files in os.walk(zrodlo):
        for file in files:
            if file.endswith('.json'):
                pelna_sciezka = os.path.join(root, file)
                wszystkie_pliki_json.append(pelna_sciezka)
    
    if not wszystkie_pliki_json:
        print("Nie znaleziono żadnych plików .json w folderze źródłowym.")
        return
        
    print(f"Znaleziono {len(wszystkie_pliki_json)} plików .json do przetworzenia.")

    # 3. Utwórz główny folder docelowy
    os.makedirs(cel, exist_ok=True)
    print(f"Utworzono lub potwierdzono istnienie folderu docelowego: '{cel}'")

    # 4. Przetwarzaj i kopiuj pliki w paczkach
    for i, sciezka_pliku_zrodlowego in enumerate(wszystkie_pliki_json):
        # Oblicz numer folderu docelowego (zaczynając od 1)
        numer_folderu = (i // rozmiar_paczki) + 1
        folder_docelowy_paczki = os.path.join(cel, str(numer_folderu))
        
        # Utwórz podfolder dla bieżącej paczki, jeśli nie istnieje
        os.makedirs(folder_docelowy_paczki, exist_ok=True)

        # Przygotuj ścieżkę docelową dla pliku
        nazwa_pliku = os.path.basename(sciezka_pliku_zrodlowego)
        sciezka_pliku_docelowego = os.path.join(folder_docelowy_paczki, nazwa_pliku)

        try:
            # Wczytaj oryginalny plik, zachowując kolejność kluczy
            with open(sciezka_pliku_zrodlowego, 'r', encoding='utf-8') as f_in:
                dane_pliku = json.load(f_in, object_pairs_hook=OrderedDict)

            # Przygotuj nowe dane z dodatkowym parametrem na początku
            nowe_dane = OrderedDict()
            
            # Oblicz i dodaj ścieżkę względną
            sciezka_wzgledna = os.path.relpath(sciezka_pliku_zrodlowego, os.path.dirname(zrodlo))
            nowe_dane['sciezka'] = sciezka_wzgledna.replace('\\', '/') # Ujednolicenie separatorów
            
            # Dodaj resztę oryginalnych danych
            nowe_dane.update(dane_pliku)

            # Zapisz zmodyfikowany plik w nowej lokalizacji
            with open(sciezka_pliku_docelowego, 'w', encoding='utf-8') as f_out:
                json.dump(nowe_dane, f_out, indent=2, ensure_ascii=False)
            
            print(f"Przetworzono i skopiowano: {nazwa_pliku} -> {folder_docelowy_paczki}")

        except Exception as e:
            print(f"BŁĄD podczas przetwarzania pliku '{sciezka_pliku_zrodlowego}': {e}")

    print("\nOperacja zakończona pomyślnie.")


def main():
    """Główna funkcja sterująca wykonaniem skryptu."""
    
    # Ustalenie ścieżek względem lokalizacji skryptu
    biezacy_folder = os.path.dirname(os.path.abspath(__file__))
    sciezka_zrodlowa = os.path.join(biezacy_folder, FOLDER_ZRODLOWY)
    sciezka_docelowa = os.path.join(biezacy_folder, FOLDER_DOCELOWY)

    reorganizuj_i_kopiuj_pliki(sciezka_zrodlowa, sciezka_docelowa, PLIKOW_W_FOLDERZE)


if __name__ == '__main__':
    main()