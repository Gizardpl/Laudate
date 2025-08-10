import os
import json
from collections import OrderedDict

# --- Konfiguracja ---
# Nazwa folderu źródłowego (o jeden poziom wyżej niż skrypt)
FOLDER_ZRODLOWY = '../Lekcjonarz_JSON2'

# Nazwa pliku JSON zawierającego listę już przetworzonych plików
PLIK_Z_POPRAWKAMI = 'gotowe.json'

# Nazwa folderu docelowego, który zostanie utworzony dla brakujących plików
FOLDER_DOCELOWY = 'poprawki'


def znajdz_i_kopiuj_brakujace(folder_zrodlowy: str, plik_z_poprawkami: str, folder_docelowy: str):
    """
    Porównuje pliki w folderze źródłowym z listą w pliku poprawek,
    a brakujące pliki kopiuje do folderu docelowego, dodając do nich ścieżkę.

    Args:
        folder_zrodlowy (str): Ścieżka do folderu Lekcjonarz_JSON2.
        plik_z_poprawkami (str): Ścieżka do pliku gotowe.json.
        folder_docelowy (str): Nazwa folderu, gdzie trafią brakujące pliki.
    """
    # 1. Wczytaj listę już przetworzonych ścieżek z pliku gotowe.json
    try:
        with open(plik_z_poprawkami, 'r', encoding='utf-8') as f:
            dane_poprawek = json.load(f)
        sciezki_przetworzone = {item['sciezka'] for item in dane_poprawek if 'sciezka' in item}
        print(f"Znaleziono {len(sciezki_przetworzone)} przetworzonych ścieżek w pliku '{plik_z_poprawkami}'.")
    except FileNotFoundError:
        print(f"Ostrzeżenie: Plik '{plik_z_poprawkami}' nie istnieje. Wszystkie pliki zostaną potraktowane jako brakujące.")
        sciezki_przetworzone = set()
    except Exception as e:
        print(f"BŁĄD podczas odczytu pliku '{plik_z_poprawkami}': {e}. Przerwanie operacji.")
        return

    # 2. Zbierz listę wszystkich plików .json z folderu źródłowego
    sciezki_zrodlowe = []
    if not os.path.isdir(folder_zrodlowy):
        print(f"BŁĄD: Folder źródłowy '{folder_zrodlowy}' nie istnieje.")
        return
        
    for root, _, files in os.walk(folder_zrodlowy):
        for file in files:
            if file.endswith('.json'):
                pelna_sciezka = os.path.join(root, file)
                # Utwórz ścieżkę względną w formacie 'Lekcjonarz_JSON2/...'
                sciezka_wzgledna = os.path.relpath(pelna_sciezka, os.path.dirname(folder_zrodlowy))
                sciezki_zrodlowe.append(sciezka_wzgledna.replace('\\', '/'))

    print(f"Znaleziono {len(sciezki_zrodlowe)} wszystkich plików .json w '{folder_zrodlowy}'.")

    # 3. Zidentyfikuj brakujące pliki
    sciezki_do_skopiowania = [sciezka for sciezka in sciezki_zrodlowe if sciezka not in sciezki_przetworzone]

    if not sciezki_do_skopiowania:
        print("Wszystkie pliki z folderu źródłowego są już zawarte w pliku 'gotowe.json'. Brak plików do skopiowania.")
        return

    print(f"Znaleziono {len(sciezki_do_skopiowania)} plików, których brakuje w pliku 'gotowe.json'. Rozpoczynam kopiowanie...")

    # 4. Utwórz folder docelowy i kopiuj brakujące pliki
    os.makedirs(folder_docelowy, exist_ok=True)
    for sciezka_wzgledna in sciezki_do_skopiowania:
        sciezka_zrodlowa_pliku = os.path.join(os.path.dirname(folder_zrodlowy), sciezka_wzgledna)
        nazwa_pliku = os.path.basename(sciezka_zrodlowa_pliku)
        sciezka_docelowa_pliku = os.path.join(folder_docelowy, nazwa_pliku)

        try:
            # Wczytaj oryginalny plik, zachowując kolejność kluczy
            with open(sciezka_zrodlowa_pliku, 'r', encoding='utf-8') as f_in:
                oryginalne_dane = json.load(f_in, object_pairs_hook=OrderedDict)

            # Przygotuj nowe dane z dodaną ścieżką na początku
            nowe_dane = OrderedDict()
            nowe_dane['sciezka'] = sciezka_wzgledna
            nowe_dane.update(oryginalne_dane)

            # Zapisz zmodyfikowany plik w nowej lokalizacji
            with open(sciezka_docelowa_pliku, 'w', encoding='utf-8') as f_out:
                json.dump(nowe_dane, f_out, indent=2, ensure_ascii=False)
            
            print(f"Skopiowano i zmodyfikowano: {nazwa_pliku} -> {folder_docelowy}")

        except Exception as e:
            print(f"BŁĄD przy przetwarzaniu pliku '{nazwa_pliku}': {e}")

    print(f"\nOperacja zakończona. Skopiowano {len(sciezki_do_skopiowania)} brakujących plików do folderu '{folder_docelowy}'.")


def main():
    """Główna funkcja sterująca wykonaniem skryptu."""
    biezacy_folder = os.path.dirname(os.path.abspath(__file__))
    sciezka_zrodlowa = os.path.join(biezacy_folder, FOLDER_ZRODLOWY)
    sciezka_do_poprawek = os.path.join(biezacy_folder, PLIK_Z_POPRAWKAMI)
    sciezka_docelowa = os.path.join(biezacy_folder, FOLDER_DOCELOWY)

    znajdz_i_kopiuj_brakujace(sciezka_zrodlowa, sciezka_do_poprawek, sciezka_docelowa)


if __name__ == '__main__':
    main()