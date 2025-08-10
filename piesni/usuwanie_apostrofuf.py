import os

# Usuwa niepotrzebne apostrofy z pliku JSON (związane z cytowaniem)

# --- Konfiguracja ---
# Nazwa pliku wejściowego z błędami
NAZWA_PLIKU_WEJSCIOWEGO = 'poprawione.json'

# Nazwa pliku wyjściowego, który zostanie utworzony z poprawioną treścią
NAZWA_PLIKU_WYJSCIOWEGO = 'gotowe.json'


def napraw_cytaty_w_json(sciezka_wejsciowa: str, sciezka_wyjsciowa: str):
    """
    Czyta plik JSON linia po linii jako tekst, naprawia zagnieżdżone
    cudzysłowy w wartościach i zapisuje wynik do nowego pliku.

    Args:
        sciezka_wejsciowa (str): Ścieżka do pliku z błędami.
        sciezka_wyjsciowa (str): Ścieżka do pliku, gdzie zostanie zapisany wynik.
    """
    # Sprawdzenie, czy plik wejściowy istnieje
    if not os.path.exists(sciezka_wejsciowa):
        print(f"BŁĄD: Plik wejściowy '{sciezka_wejsciowa}' nie został znaleziony.")
        return

    print(f"Rozpoczynam przetwarzanie pliku '{sciezka_wejsciowa}'...")
    licznik_linii_przetworzonych = 0
    licznik_linii_naprawionych = 0

    # Otwarcie plików do odczytu i zapisu
    with open(sciezka_wejsciowa, 'r', encoding='utf-8') as plik_wejsciowy, \
         open(sciezka_wyjsciowa, 'w', encoding='utf-8') as plik_wyjsciowy:
        
        for linia in plik_wejsciowy:
            licznik_linii_przetworzonych += 1
            
            # Zachowanie oryginalnego wcięcia
            wciencie = linia[:len(linia) - len(linia.lstrip())]
            linia_bez_wcienc = linia.strip()

            # Podział linii na klucz i wartość na podstawie pierwszego dwukropka
            try:
                klucz, wartosc_z_przecinkiem = linia_bez_wcienc.split(':', 1)
            except ValueError:
                # Jeśli linia nie zawiera dwukropka (np. '{', '}' lub pusta linia), zapisz ją bez zmian
                plik_wyjsciowy.write(linia)
                continue

            # Interesują nas tylko wartości tekstowe (zaczynające się od cudzysłowu)
            wartosc_oczyszczona = wartosc_z_przecinkiem.strip()
            if not wartosc_oczyszczona.startswith('"'):
                plik_wyjsciowy.write(linia)
                continue

            # Sprawdzenie, czy w wartości jest więcej niż 2 cudzysłowy (co wskazuje na zagnieżdżenie)
            if wartosc_oczyszczona.count('"') > 2:
                # Ustalenie, czy na końcu linii jest przecinek
                czy_ma_przecinek = wartosc_oczyszczona.endswith(',')
                
                # Wyizolowanie treści wewnątrz zewnętrznych cudzysłowów
                if czy_ma_przecinek:
                    # Treść znajduje się między pierwszym a przedostatnim znakiem
                    tresc = wartosc_oczyszczona[1:-2]
                else:
                    # Treść znajduje się między pierwszym a ostatnim znakiem
                    tresc = wartosc_oczyszczona[1:-1]
                
                # Zamiana wszystkich wewnętrznych cudzysłowów na apostrofy
                naprawiona_tresc = tresc.replace('"', "'")
                
                # Odtworzenie części z wartością
                if czy_ma_przecinek:
                    naprawiona_wartosc = f'"{naprawiona_tresc}",'
                else:
                    naprawiona_wartosc = f'"{naprawiona_tresc}"'
                
                # Odtworzenie całej linii z zachowaniem wcięcia i klucza
                nowa_linia = f"{wciencie}{klucz}: {naprawiona_wartosc}\n"
                plik_wyjsciowy.write(nowa_linia)
                licznik_linii_naprawionych += 1
            else:
                # Jeśli linia jest poprawna, zapisz ją bez zmian
                plik_wyjsciowy.write(linia)

    print("\nOperacja zakończona.")
    print(f"Przetworzono linii: {licznik_linii_przetworzonych}")
    print(f"Naprawiono linii: {licznik_linii_naprawionych}")
    print(f"Poprawiony plik został zapisany jako '{sciezka_wyjsciowa}'.")


def main():
    """Główna funkcja sterująca wykonaniem skryptu."""
    biezacy_folder = os.path.dirname(os.path.abspath(__file__))
    sciezka_pliku_wejsciowego = os.path.join(biezacy_folder, NAZWA_PLIKU_WEJSCIOWEGO)
    sciezka_pliku_wyjsciowego = os.path.join(biezacy_folder, NAZWA_PLIKU_WYJSCIOWEGO)
    
    napraw_cytaty_w_json(sciezka_pliku_wejsciowego, sciezka_pliku_wyjsciowego)


if __name__ == '__main__':
    main()