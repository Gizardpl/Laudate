import json
import os

# --- KONFIGURACJA SKRYPTU ---
# W tym miejscu zdefiniowane są wszystkie parametry, które można łatwo modyfikować.
CONFIG = {
    # Nazwa wejściowego pliku JSON z listą wszystkich pieśni
    "plik_wejsciowy_piesni": "piesni.json",
    
    # Nazwa wejściowego pliku JSON z listą poprawek (tytulPoprawny, tytulZly)
    "plik_wejsciowy_poprawki": "poprawki.json",
    
    # Nazwa pliku, do którego zostanie zapisany wynik
    "plik_wyjsciowy": "piesni_finalne.json",
    
    # Nazwa klucza w pliku poprawek, który przechowuje poprawny tytuł
    "klucz_tytul_poprawny": "tytulPoprawny",
    
    # Nazwa klucza w pliku poprawek, który przechowuje błędny tytuł
    "klucz_tytul_zly": "tytulZly",

    # Nazwa klucza w głównym pliku pieśni, który przechowuje tytuł
    "klucz_tytul_piesni": "tytul" 
}
# --- KONIEC KONFIGURACJI ---


def polacz_dane_piesni(config):
    """
    Przetwarza listę pieśni na podstawie pliku z poprawkami, łącząc zduplikowane wpisy.
    Wszystkie parametry operacji pobierane są ze słownika konfiguracyjnego.

    Args:
        config (dict): Słownik zawierający konfigurację ścieżek do plików i nazw kluczy.
    """
    try:
        # --- Krok 1: Wczytanie danych z plików JSON przy użyciu konfiguracji ---
        with open(config["plik_wejsciowy_piesni"], 'r', encoding='utf-8') as f:
            dane_piesni = json.load(f)
        
        with open(config["plik_wejsciowy_poprawki"], 'r', encoding='utf-8') as f:
            dane_poprawek = json.load(f)

        print(f"Wczytano {len(dane_piesni)} pieśni i {len(dane_poprawek)} reguł poprawek.")

        # --- Krok 2: Konwersja listy pieśni na słownik dla szybkiego dostępu ---
        # Kluczem jest tytuł pieśni, a wartością cały obiekt pieśni.
        slownik_piesni = {song[config["klucz_tytul_piesni"]]: song for song in dane_piesni}
        
        # Zbiór na tytuły pieśni, które zostaną usunięte po scaleniu
        tytuly_do_usuniecia = set()

        # --- Krok 3: Iteracja po liście poprawek i przetwarzanie danych ---
        for poprawka in dane_poprawek:
            poprawny_tytul = poprawka.get(config["klucz_tytul_poprawny"])
            zly_tytul = poprawka.get(config["klucz_tytul_zly"])

            # Pomijamy wpisy, w których brakuje jednego z tytułów (są puste)
            if not poprawny_tytul or not zly_tytul:
                continue

            # Sprawdzamy, czy obie pieśni (poprawna i zła) istnieją w naszym zbiorze
            if poprawny_tytul in slownik_piesni and zly_tytul in slownik_piesni:
                
                # Pobieramy obiekty obu pieśni
                poprawna_piesn = slownik_piesni[poprawny_tytul]
                zla_piesn = slownik_piesni[zly_tytul]

                print(f"Przetwarzanie: '{zly_tytul}' -> '{poprawny_tytul}'")

                # --- Krok 4: Przepisywanie danych z pieśni "złej" do "poprawnej" ---
                for klucz, wartosc in zla_piesn.items():
                    # Ignorujemy klucz tytułu, aby nie nadpisać poprawnego
                    if klucz == config["klucz_tytul_piesni"]:
                        continue
                    
                    # Przepisujemy wartość tylko wtedy, gdy nie jest pusta.
                    # Ten warunek (`if wartosc`) obsługuje puste stringi, listy, itp.
                    if wartosc:
                        poprawna_piesn[klucz] = wartosc
                
                # Dodajemy tytuł "złej" pieśni do zbioru do usunięcia
                tytuly_do_usuniecia.add(zly_tytul)

            else:
                # Informacja, jeśli którejś z pieśni nie znaleziono
                if poprawny_tytul not in slownik_piesni:
                    print(f"OSTRZEŻENIE: Nie znaleziono pieśni o poprawnym tytule: '{poprawny_tytul}'")
                if zly_tytul not in slownik_piesni:
                    print(f"OSTRZEŻENIE: Nie znaleziono pieśni o błędnym tytule: '{zly_tytul}'")
        
        # --- Krok 5: Tworzenie nowej, finalnej listy pieśni ---
        finalna_lista_piesni = [
            piesn for tytul, piesn in slownik_piesni.items() 
            if tytul not in tytuly_do_usuniecia
        ]
        
        # --- Krok 6: Zapisanie przetworzonych danych do nowego pliku JSON ---
        with open(config["plik_wyjsciowy"], 'w', encoding='utf-8') as f:
            json.dump(finalna_lista_piesni, f, ensure_ascii=False, indent=4)
            
        print(f"\nPrzetwarzanie zakończone. Usunięto {len(tytuly_do_usuniecia)} zduplikowanych pieśni.")
        print(f"Nowy plik z {len(finalna_lista_piesni)} pieśniami został zapisany jako: '{config['plik_wyjsciowy']}'")

    except FileNotFoundError as e:
        print(f"BŁĄD: Nie znaleziono pliku: {e.filename}. Upewnij się, że pliki wejściowe znajdują się w tym samym folderze co skrypt.")
    except json.JSONDecodeError as e:
        print(f"BŁĄD: Plik nie jest poprawnym plikiem JSON. Błąd: {e}")
    except KeyError as e:
        print(f"BŁĄD: W danych brakuje oczekiwanego klucza: {e}. Sprawdź pliki JSON oraz konfigurację skryptu.")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")


# --- Uruchomienie skryptu ---
if __name__ == "__main__":
    # Wywołanie głównej funkcji z przekazaniem obiektu konfiguracji
    polacz_dane_piesni(CONFIG)