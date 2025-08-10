import json

#Tworzy slownik pieśni z pliku JSON

# Definicja nazw plików
plik_wejsciowy = 'piesni.json'
plik_wyjsciowy = 'slownik.json'

try:
    # Otwarcie pliku źródłowego do odczytu
    with open(plik_wejsciowy, 'r', encoding='utf-8') as f_in:
        dane_wejsciowe = json.load(f_in)

    # Przygotowanie nowej listy na przetworzone dane
    dane_wyjsciowe = []

    # Sprawdzenie, czy wczytane dane są listą
    if isinstance(dane_wejsciowe, list):
        # Pętla przez wszystkie obiekty (pieśni) w liście
        for piesn in dane_wejsciowe:
            # Utworzenie nowego obiektu tylko z polami 'tytul' i 'numer'
            nowy_obiekt = {
                'tytul': piesn.get('tytul'),
                'numer': piesn.get('numer')
            }
            dane_wyjsciowe.append(nowy_obiekt)

        # Otwarcie pliku docelowego do zapisu
        with open(plik_wyjsciowy, 'w', encoding='utf-8') as f_out:
            # Zapisanie nowej listy do pliku JSON z formatowaniem
            json.dump(dane_wyjsciowe, f_out, ensure_ascii=False, indent=2)

        print(f"Przetwarzanie zakończone. Usunięto pole 'tekst' i zapisano wynik do pliku: {plik_wyjsciowy}")

    else:
        print("Błąd: Plik źródłowy nie zawiera listy obiektów.")

except FileNotFoundError:
    print(f"Błąd: Nie można znaleźć pliku '{plik_wejsciowy}'. Upewnij się, że plik znajduje się w tym samym folderze co skrypt.")
except json.JSONDecodeError:
    print(f"Błąd: Plik '{plik_wejsciowy}' nie jest poprawnym plikiem JSON.")
except Exception as e:
    print(f"Wystąpił nieoczekiwany błąd: {e}")