import json

#Liczy ile obiektów zawira plik JSON

# Nazwa pliku, który ma zostać przeanalizowany
nazwa_pliku = 'gotowe.json'

try:
    # Otwieranie pliku JSON w trybie do odczytu ('r') z kodowaniem UTF-8
    with open(nazwa_pliku, 'r', encoding='utf-8') as plik:
        # Wczytanie danych z pliku JSON do zmiennej w Pythonie
        dane = json.load(plik)

        # Sprawdzenie, czy wczytane dane są listą (plik JSON zaczyna się od '[')
        if isinstance(dane, list):
            # Obliczenie liczby obiektów w liście
            liczba_obiektow = len(dane)
            # Wypisanie samej liczby na ekranie
            print(liczba_obiektow)
        else:
            # Komunikat, jeśli plik nie zawiera listy na najwyższym poziomie
            print("Błąd: Plik JSON nie zawiera listy obiektów.")

except FileNotFoundError:
    # Obsługa błędu, gdy plik o podanej nazwie nie istnieje
    print(f"Błąd: Nie znaleziono pliku o nazwie '{nazwa_pliku}'.")
except json.JSONDecodeError:
    # Obsługa błędu, gdy plik nie jest poprawnym plikiem JSON
    print(f"Błąd: Plik '{nazwa_pliku}' ma niepoprawną strukturę JSON lub jest uszkodzony.")
except Exception as e:
    # Obsługa innych, nieoczekiwanych błędów
    print(f"Wystąpił nieoczekiwany błąd: {e}")