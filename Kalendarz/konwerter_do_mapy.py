import json

def konwertuj_json_na_mape(nazwa_pliku_wejsciowego, nazwa_pliku_wyjsciowego):
    """
    Wczytuje plik JSON, zamienia w każdej linii dwukropek na ' to '
    i zapisuje wynik do pliku tekstowego.

    Args:
        nazwa_pliku_wejsciowego (str): Nazwa pliku JSON do przetworzenia.
        nazwa_pliku_wyjsciowego (str): Nazwa pliku TXT, w którym zostanie zapisany wynik.
    """
    print(f"Rozpoczynam przetwarzanie pliku: '{nazwa_pliku_wejsciowego}'...")

    try:
        # Krok 1: Otwórz plik wejściowy do odczytu
        with open(nazwa_pliku_wejsciowego, 'r', encoding='utf-8') as plik_wejsciowy:
            # Krok 2: Otwórz plik wyjściowy do zapisu
            with open(nazwa_pliku_wyjsciowego, 'w', encoding='utf-8') as plik_wyjsciowy:

                # Krok 3: Przejdź przez każdą linię w pliku wejściowym
                for linia in plik_wejsciowy:
                    # Sprawdź, czy w linii znajduje się dwukropek
                    if ':' in linia:
                        # Zamień pierwszy napotkany dwukropek na ' to'
                        try:
                            # Znajdź indeks drugiego cudzysłowu
                            indeks_konca_klucza = linia.find('"', linia.find('"') + 1)
                            
                            # Podziel linię
                            klucz = linia[:indeks_konca_klucza + 1]
                            reszta_linii = linia[indeks_konca_klucza + 1:]
                            
                            # Dokonaj zamiany tylko w drugiej części
                            reszta_linii_poprawiona = reszta_linii.replace(':', ' to', 1)
                            
                            # Połącz wszystko z powrotem
                            nowa_linia = klucz + reszta_linii_poprawiona
                        except IndexError:
                            # Zabezpieczenie na wypadek dziwnie sformatowanej linii
                            nowa_linia = linia
                    else:
                        # Jeśli w linii nie ma dwukropka, przepisz ją bez zmian
                        nowa_linia = linia

                    # Zapisz zmodyfikowaną (lub oryginalną) linię do pliku wyjściowego
                    plik_wyjsciowy.write(nowa_linia)

        print(f"Sukces! Wynik został zapisany do pliku '{nazwa_pliku_wyjsciowego}'.")

    except FileNotFoundError:
        print(f"BŁĄD: Nie znaleziono pliku '{nazwa_pliku_wejsciowego}'. Upewnij się, że plik znajduje się w tym samym folderze co skrypt.")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")

# --- Uruchomienie skryptu ---
if __name__ == "__main__":
    # Nazwy plików są teraz ustawione zgodnie z Twoimi wymaganiami
    plik_json_do_przetworzenia = "slownik_poprawiony_i_odwrocony.json"
    plik_wynikowy_txt = "mapa.txt"
    
    konwertuj_json_na_mape(plik_json_do_przetworzenia, plik_wynikowy_txt)