import json
import re

# ==============================================================================
# STAŁE KONFIGURACYJNE
# ==============================================================================
INPUT_FILENAME = 'piesni3.json'
OUTPUT_FILENAME = 'piesni4.json'
FILE_ENCODING = 'utf-8'
JSON_INDENTATION = 4

def format_song_text(text):
    """
    Funkcja formatująca tekst pieśni. Wstawia znak nowej linii (\n) przed
    słowami kluczowymi ('Refren', 'Ref') oraz numerami zwrotek (np. '1.'),
    ale tylko wtedy, gdy nie ma już tam nowej linii i nie jest to początek tekstu.
    """
    # Wzorzec wyszukujący "Refren", "Ref" lub cyfry zakończone kropką
    pattern = r'(Refren|Ref|\d+\.)'
    
    # Przechowuje pozycję końca ostatniego znalezionego dopasowania
    last_end = 0
    # Lista, do której będziemy dodawać fragmenty przetworzonego tekstu
    parts = []
    
    # re.finditer znajduje wszystkie wystąpienia wzorca i zwraca iterator obiektów 'match'
    for match in re.finditer(pattern, text):
        start = match.start()
        
        # Dodaj fragment tekstu znajdujący się przed bieżącym dopasowaniem
        parts.append(text[last_end:start])
        
        # Sprawdź warunki, czy należy dodać nową linię
        # 1. start > 0: Dopasowanie nie jest na samym początku tekstu
        # 2. text[start-1] != '\n': Znak bezpośrednio przed dopasowaniem nie jest znakiem nowej linii
        if start > 0 and text[start-1] != '\n':
            parts.append('\n')
            
        # Dodaj znaleziony fragment (np. "Refren" lub "1.")
        parts.append(match.group(0))
        
        # Zaktualizuj pozycję końca
        last_end = match.end()
        
    # Dodaj pozostałą część tekstu po ostatnim dopasowaniu
    parts.append(text[last_end:])
    
    # Połącz wszystkie fragmenty w jeden ciąg znaków
    return "".join(parts)

def main():
    """Główna funkcja skryptu formatującego."""
    print("--- Skrypt 1: Formatowanie tekstu pieśni ---")
    if not os.path.exists(INPUT_FILENAME):
        print(f"BŁĄD: Plik wejściowy '{INPUT_FILENAME}' nie został znaleziony.")
        return

    try:
        # Odczyt danych z pliku wejściowego
        with open(INPUT_FILENAME, 'r', encoding=FILE_ENCODING) as f:
            data = json.load(f)

        print(f"Wczytano {len(data)} pieśni z pliku '{INPUT_FILENAME}'. Rozpoczynam formatowanie...")

        # Przetwarzanie każdego obiektu (słownika) w liście
        for song in data:
            if 'tekst' in song and isinstance(song['tekst'], str):
                song['tekst'] = format_song_text(song['tekst'])

        # Zapis zmodyfikowanych danych do pliku wyjściowego
        with open(OUTPUT_FILENAME, 'w', encoding=FILE_ENCODING) as f:
            json.dump(data, f, indent=JSON_INDENTATION, ensure_ascii=False)

        print(f"Formatowanie zakończone. Wynik zapisano w pliku '{OUTPUT_FILENAME}'.")

    except json.JSONDecodeError:
        print(f"BŁĄD: Plik '{INPUT_FILENAME}' ma nieprawidłowy format JSON.")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")

if __name__ == "__main__":
    import os
    main()