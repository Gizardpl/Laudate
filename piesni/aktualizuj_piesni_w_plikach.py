import os
import json

# Na podstawie pliku z danymi od Gemini aktualizuje pieśni w docelowej lokalizacji

# --- Konfiguracja ---
# Nazwa pliku wejściowego zawierającego poprawione dane
NAZWA_PLIKU_Z_POPRAWKAMI = 'gotowe.json'

# Ścieżka bazowa, gdzie znajduje się główny folder z lekcjonarzem
# '../' oznacza jeden folder w górę od lokalizacji skryptu
KATALOG_BAZOWY_LEKCJONARZA = '../'


def zastosuj_poprawki(sciezka_do_poprawek: str):
    """
    Wczytuje plik z poprawkami i aktualizuje odpowiednie pliki docelowe,
    nadpisując w nich sekcję 'piesniSugerowane'.

    Args:
        sciezka_do_poprawek (str): Ścieżka do pliku JSON z poprawkami.
    """
    # 1. Wczytaj plik z poprawkami
    try:
        with open(sciezka_do_poprawek, 'r', encoding='utf-8') as f:
            dane_z_poprawkami = json.load(f)
        print(f"Pomyślnie wczytano plik z poprawkami: '{sciezka_do_poprawek}'.")
    except FileNotFoundError:
        print(f"BŁĄD KRYTYCZNY: Nie można znaleźć pliku z poprawkami: '{sciezka_do_poprawek}'. Przerwanie operacji.")
        return
    except json.JSONDecodeError:
        print(f"BŁĄD KRYTYCZNY: Plik '{sciezka_do_poprawek}' ma nieprawidłowy format JSON. Przerwanie operacji.")
        return
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas odczytu pliku z poprawkami: {e}")
        return

    if not isinstance(dane_z_poprawkami, list):
        print("BŁĄD KRYTYCZNY: Plik z poprawkami nie zawiera listy obiektów.")
        return

    licznik_zaktualizowanych = 0
    licznik_niepowodzen = 0
    
    # 2. Przetwórz każdy obiekt (każdą poprawkę) z pliku
    for wpis in dane_z_poprawkami:
        sciezka_wzgledna = wpis.get("sciezka")
        nowe_dane_piesni = wpis.get("piesniSugerowane")

        if not sciezka_wzgledna or nowe_dane_piesni is None:
            print(f"Ostrzeżenie: Pomijam niekompletny wpis w pliku z poprawkami: {wpis}")
            licznik_niepowodzen += 1
            continue

        # Zbuduj pełną ścieżkę do pliku, który ma zostać zaktualizowany
        sciezka_pliku_docelowego = os.path.normpath(os.path.join(KATALOG_BAZOWY_LEKCJONARZA, sciezka_wzgledna))

        try:
            # Wczytaj zawartość oryginalnego pliku
            with open(sciezka_pliku_docelowego, 'r', encoding='utf-8') as f:
                oryginalne_dane_pliku = json.load(f)

            # Podmień sekcję z pieśniami na nową, poprawioną wersję
            oryginalne_dane_pliku['piesniSugerowane'] = nowe_dane_piesni

            # Zapisz (nadpisz) plik z powrotem z nowymi danymi
            with open(sciezka_pliku_docelowego, 'w', encoding='utf-8') as f:
                json.dump(oryginalne_dane_pliku, f, indent=2, ensure_ascii=False)
            
            licznik_zaktualizowanych += 1
            print(f"OK: Zaktualizowano plik '{sciezka_pliku_docelowego}'")

        except FileNotFoundError:
            print(f"BŁĄD: Nie znaleziono pliku docelowego: '{sciezka_pliku_docelowego}'. Pomijam.")
            licznik_niepowodzen += 1
        except KeyError:
            print(f"BŁĄD: W pliku '{sciezka_pliku_docelowego}' brakuje klucza 'piesniSugerowane'. Nie można dokonać podmiany.")
            licznik_niepowodzen += 1
        except Exception as e:
            print(f"BŁĄD podczas przetwarzania pliku '{sciezka_pliku_docelowego}': {e}")
            licznik_niepowodzen += 1
            
    print("\n--- Podsumowanie ---")
    print(f"Pomyślnie zaktualizowano: {licznik_zaktualizowanych} plików.")
    if licznik_niepowodzen > 0:
        print(f"Nie udało się przetworzyć: {licznik_niepowodzen} plików (sprawdź komunikaty BŁĘDÓW/OSTRZEŻEŃ powyżej).")
    print("Operacja zakończona.")


def main():
    """Główna funkcja sterująca wykonaniem skryptu."""
    
    folder_skryptu = os.path.dirname(os.path.abspath(__file__))
    sciezka_do_pliku_poprawek = os.path.join(folder_skryptu, NAZWA_PLIKU_Z_POPRAWKAMI)

    zastosuj_poprawki(sciezka_do_pliku_poprawek)


if __name__ == '__main__':
    main()