import json
import os

# ==============================================================================
# KONFIGURACJA
# Zdefiniuj nazwy plików wejściowych i wyjściowych.
# ==============================================================================

# Plik źródłowy z numerami DN
DN_FILENAME = 'DN.json'

# Główny plik z pieśniami, który będzie aktualizowany
PIESNI_INPUT_FILENAME = 'piesni.json'

# Nazwa pliku wyjściowego, który zostanie utworzony po przetworzeniu
PIESNI_OUTPUT_FILENAME = 'piesni_zaktualizowany.json'

# Kodowanie znaków używane we wszystkich plikach
FILE_ENCODING = 'utf-8'

# Wcięcie dla wynikowego pliku JSON (dla lepszej czytelności)
JSON_INDENTATION = 4


def update_songs_database():
    """
    Główna funkcja skryptu. Wczytuje dane z plików DN.json i piesni.json,
    aktualizuje lub dodaje wpisy, a następnie zapisuje wynik do nowego pliku.
    """
    
    # --- Krok 1: Sprawdzenie, czy pliki wejściowe istnieją ---
    if not os.path.exists(DN_FILENAME):
        print(f"BŁĄD: Plik wejściowy '{DN_FILENAME}' nie został znaleziony. Przerwanie działania.")
        return
        
    if not os.path.exists(PIESNI_INPUT_FILENAME):
        print(f"BŁĄD: Plik wejściowy '{PIESNI_INPUT_FILENAME}' nie został znaleziony. Przerwanie działania.")
        return

    print("Rozpoczynam proces aktualizacji bazy pieśni...")

    # --- Krok 2: Wczytanie danych z plików JSON ---
    try:
        with open(DN_FILENAME, 'r', encoding=FILE_ENCODING) as f:
            dn_data = json.load(f)
        with open(PIESNI_INPUT_FILENAME, 'r', encoding=FILE_ENCODING) as f:
            piesni_data = json.load(f)
        print(f"Pomyślnie wczytano {len(dn_data)} pieśni z '{DN_FILENAME}'.")
        print(f"Pomyślnie wczytano {len(piesni_data)} pieśni z '{PIESNI_INPUT_FILENAME}'.")
    except json.JSONDecodeError as e:
        print(f"BŁĄD: Wystąpił błąd formatu w jednym z plików JSON. Szczegóły: {e}")
        return
    except Exception as e:
        print(f"BŁĄD: Wystąpił problem podczas wczytywania plików: {e}")
        return

    # --- Krok 3: Stworzenie mapy tytułów dla optymalizacji wyszukiwania ---
    # Kluczem jest tytuł, a wartością indeks pieśni w liście piesni_data.
    title_to_index_map = {song['tytul'].strip(): i for i, song in enumerate(piesni_data)}
    
    # Liczniki do podsumowania operacji
    updated_count = 0
    added_count = 0

    # --- Krok 4: Iteracja przez dane z DN.json i aktualizacja bazy pieśni ---
    print("Przetwarzanie pieśni i aktualizacja danych...")
    for dn_song in dn_data:
        tytul = dn_song.get('tytul', '').strip()
        numer_dn = dn_song.get('numerDN', '')

        if not tytul:
            continue  # Pomiń wpisy bez tytułu

        # Sprawdzenie, czy pieśń o danym tytule już istnieje w bazie
        if tytul in title_to_index_map:
            # AKTUALIZACJA: Pieśń istnieje, więc aktualizujemy jej numerDN
            song_index = title_to_index_map[tytul]
            piesni_data[song_index]['numerDN'] = numer_dn
            updated_count += 1
        else:
            # DODAWANIE: Pieśni nie ma w bazie, więc tworzymy nowy obiekt
            new_song = {
                "tytul": tytul,
                "tekst": "",
                "numerSiedl": "",
                "numerSAK": "",
                "numerDN": numer_dn,
                "kategoria": "",
                "kategoriaSkr": ""
            }
            piesni_data.append(new_song)
            added_count += 1
            
    # --- Krok 5: Zapisanie zaktualizowanych danych do nowego pliku ---
    print("\nZakończono przetwarzanie. Podsumowanie:")
    print(f" - Zaktualizowano numerDN dla {updated_count} istniejących pieśni.")
    print(f" - Dodano {added_count} nowych pieśni do bazy.")
    
    try:
        with open(PIESNI_OUTPUT_FILENAME, 'w', encoding=FILE_ENCODING) as f:
            json.dump(piesni_data, f, indent=JSON_INDENTATION, ensure_ascii=False)
        print(f"\nOperacja zakończona pomyślnie! Zaktualizowana baza została zapisana w pliku '{PIESNI_OUTPUT_FILENAME}'.")
    except Exception as e:
        print(f"BŁĄD: Wystąpił problem podczas zapisywania pliku wyjściowego: {e}")

# Uruchomienie głównej funkcji skryptu
if __name__ == "__main__":
    update_songs_database()