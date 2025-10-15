import json

# --- Konfiguracja ---
# Nazwa nowego parametru, który zostanie dodany do każdego obiektu.
NEW_PARAMETER_NAME = "numerNT2"

# Domyślna wartość dla nowego parametru.
NEW_PARAMETER_VALUE = ""

# Nazwa parametru, po którym zostanie wstawiony nowy parametr.
AFTER_PARAMETER = "numerNT2"

# Nazwa pliku wejściowego i wyjściowego
INPUT_FILE = "piesni1.json"
OUTPUT_FILE = "piesni1.json"
# --- Koniec Konfiguracji ---

def add_parameter_to_json(input_file, output_file, new_param_name, new_param_value, after_param):
    """
    Funkcja wczytuje plik JSON, dodaje nowy parametr do każdego obiektu
    i zapisuje zmiany w nowym pliku.
    """
    try:
        # Wczytanie danych z pliku JSON
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        updated_data = []
        for item in data:
            new_item = {}
            for key, value in item.items():
                new_item[key] = value
                # Wstawienie nowego parametru po określonym kluczu
                if key == after_param:
                    new_item[new_param_name] = new_param_value
            updated_data.append(new_item)

        # Zapisanie zaktualizowanych danych do nowego pliku JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)

        print(f"Pomyślnie przetworzono plik. Zaktualizowane dane zostały zapisane w '{output_file}'.")

    except FileNotFoundError:
        print(f"Błąd: Plik '{input_file}' nie został znaleziony.")
    except json.JSONDecodeError:
        print(f"Błąd: Plik '{input_file}' ma nieprawidłowy format JSON.")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")

# Wywołanie funkcji
add_parameter_to_json(INPUT_FILE, OUTPUT_FILE, NEW_PARAMETER_NAME, NEW_PARAMETER_VALUE, AFTER_PARAMETER)