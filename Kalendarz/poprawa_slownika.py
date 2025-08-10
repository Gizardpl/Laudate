import json
import re

def przetworz_slownik():
    """
    Główna funkcja, która wczytuje, filtruje, czyści, odwraca
    i zapisuje dane ze słownika JSON.
    """
    nazwa_pliku_wejsciowego = 'slownik.json'
    nazwa_pliku_wyjsciowego = 'slownik_poprawiony_i_odwrocony.json'

    try:
        with open(nazwa_pliku_wejsciowego, 'r', encoding='utf-8') as f:
            dane = json.load(f)
            print(f"Wczytano plik '{nazwa_pliku_wejsciowego}'. Rozpoczynam przetwarzanie...")
    except FileNotFoundError:
        print(f"BŁĄD: Nie znaleziono pliku '{nazwa_pliku_wejsciowego}'. Upewnij się, że znajduje się w tym samym folderze co skrypt.")
        return
    except json.JSONDecodeError:
        print(f"BŁĄD: Plik '{nazwa_pliku_wejsciowego}' ma niepoprawny format JSON.")
        return

    # === ETAP 1: Filtrowanie i czyszczenie danych ===
    dane_posrednie = {}
    for klucz, wartosc in dane.items():
        # Krok 1: Sprawdź, czy wartość jest pustym ciągiem znaków.
        # Jeśli tak, pomiń ten wpis całkowicie.
        if not wartosc: # To sprawdza zarówno None, jak i pusty string ""
            print(f"Pominięto wpis '{klucz}', ponieważ jego wartość jest pusta.")
            continue  # Przejdź do następnego elementu

        # Krok 2: Jeśli wartość nie jest pusta, oczyść klucz ze słowa "rok" i reszty.
        oczyszczony_klucz = klucz
        
        # Używamy wyrażenia regularnego, aby znaleźć " rok " (z uwzględnieniem wielkości liter)
        # i usunąć wszystko od tego miejsca do końca.
        mecz = re.search(r'\s+rok\s+', oczyszczony_klucz, re.IGNORECASE)
        if mecz:
            # Zachowaj tylko część klucza przed znalezionym dopasowaniem
            oczyszczony_klucz = oczyszczony_klucz[:mecz.start()]
        
        # Zapisz oczyszczony klucz i oryginalną wartość do tymczasowego słownika
        dane_posrednie[oczyszczony_klucz] = wartosc

    print(f"Zakończono czyszczenie i filtrowanie. Pozostało {len(dane_posrednie)} poprawnych wpisów.")

    # === ETAP 2: Odwracanie oczyszczonego słownika (zamiana kluczy z wartościami) ===
    dane_odwrocone = {}
    for stary_klucz, stara_wartosc in dane_posrednie.items():
        # Nowym kluczem staje się stara wartość
        nowy_klucz = stara_wartosc
        # Nową wartością staje się stary (oczyszczony) klucz
        nowa_wartosc = stary_klucz

        dane_odwrocone[nowy_klucz] = nowa_wartosc

    print("Zakończono odwracanie kluczy z wartościami.")

    # === ETAP 3: Zapisanie wyniku do nowego pliku ===
    try:
        with open(nazwa_pliku_wyjsciowego, 'w', encoding='utf-8') as f:
            # indent=4 sprawia, że plik JSON jest ładnie sformatowany i czytelny
            json.dump(dane_odwrocone, f, ensure_ascii=False, indent=4)
        print(f"SUKCES! Wynik został zapisany do pliku '{nazwa_pliku_wyjsciowego}'.")
    except Exception as e:
        print(f"Wystąpił błąd podczas zapisu pliku: {e}")

# Uruchomienie głównej funkcji skryptu
if __name__ == "__main__":
    przetworz_slownik()