import json
import re
import os

# ==============================================================================
# STAŁE KONFIGURACYJNE
# ==============================================================================
SAK_FILENAME = 'SAK.txt'
KATEGORIE_FILENAME = 'Kategorie.txt'
PIESNI_INPUT_FILENAME = 'piesni2.json'  # Plik wejściowy to wynik działania skryptu nr 1
PIESNI_OUTPUT_FILENAME = 'piesni3.json' # Nowy plik wyjściowy
FILE_ENCODING = 'utf-8'
JSON_INDENTATION = 4

# --- Funkcje do obsługi kategorii (tak jak w poprzedniej wersji) ---

def parse_kategorie(kategorie_content):
    ranged_categories = []
    named_categories = {}
    lines = kategorie_content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        range_match = re.match(r'(\d+)-(\d+)\s*-\s*(.+?)\s*\{(.+?)\}', line)
        named_match = re.match(r'^([^{]+?)\s*\{(.+?)\}', line)
        if range_match:
            start, end, name, abbr = range_match.groups()
            ranged_categories.append({'start': int(start), 'end': int(end), 'name': name.strip(), 'abbr': abbr.strip()})
        elif named_match:
            name, abbr = named_match.groups()
            name = name.strip()
            if not re.match(r'\d+-\d+', name):
                named_categories[name] = {'name': name, 'abbr': abbr.strip()}
    return ranged_categories, named_categories

def find_category_by_siedl(numer_siedl, ranged_categories):
    try:
        num = int(numer_siedl)
        for cat in ranged_categories:
            if cat['start'] <= num <= cat['end']:
                return cat
    except (ValueError, TypeError):
        return None
    return None

def find_category_by_name(name, ranged_categories, named_categories):
    if name in named_categories: return named_categories[name]
    for cat in ranged_categories:
        if cat['name'] == name: return cat
    return None

# --- Główna funkcja skryptu ---

def process_and_enrich_songs():
    """Wczytuje sformatowane pieśni i wzbogaca je o dane z SAK i Kategorii."""
    print("\n--- Skrypt 2: Wzbogacanie danych o pieśniach ---")
    for filename in [SAK_FILENAME, KATEGORIE_FILENAME, PIESNI_INPUT_FILENAME]:
        if not os.path.exists(filename):
            print(f"BŁĄD: Plik wejściowy '{filename}' nie został znaleziony. Uruchom najpierw skrypt nr 1.")
            return

    print(f"Wczytywanie plików: '{SAK_FILENAME}', '{KATEGORIE_FILENAME}', '{PIESNI_INPUT_FILENAME}'")
    try:
        with open(SAK_FILENAME, 'r', encoding=FILE_ENCODING) as f:
            sak_content = f.read()
        with open(KATEGORIE_FILENAME, 'r', encoding=FILE_ENCODING) as f:
            kategorie_content = f.read()
        with open(PIESNI_INPUT_FILENAME, 'r', encoding=FILE_ENCODING) as f:
            piesni_data = json.load(f)
    except Exception as e:
        print(f"BŁĄD: Wystąpił problem podczas wczytywania plików: {e}")
        return

    print("Przetwarzanie danych...")
    ranged_categories, named_categories = parse_kategorie(kategorie_content)
    title_map = {song['tytul'].strip(): i for i, song in enumerate(piesni_data)}
    
    current_sak_category_name = None
    sak_lines = sak_content.strip().split('\n')
    songs_added, songs_updated = 0, 0

    for line in sak_lines:
        line = line.strip()
        if not line: continue
        song_match = re.match(r'^(\d+)\s+(.+)$', line)
        if song_match:
            numer_sak, tytul_sak = song_match.groups()
            tytul_sak = tytul_sak.strip()
            if tytul_sak in title_map:
                song_index = title_map[tytul_sak]
                song_obj = piesni_data[song_index]
                song_obj['numerSAK'] = numer_sak.strip()
                numer_siedl = song_obj.get('numerSiedl')
                if numer_siedl:
                    category_info = find_category_by_siedl(numer_siedl, ranged_categories)
                    if category_info:
                        song_obj['kategoria'] = category_info['name']
                        song_obj['kategoriaSkr'] = category_info['abbr']
                songs_updated += 1
            else:
                new_song = {"tytul": tytul_sak, "tekst": "", "numerSiedl": "", "numerSAK": numer_sak.strip(), "numerDN": "", "kategoria": "", "kategoriaSkr": ""}
                if current_sak_category_name:
                    category_info = find_category_by_name(current_sak_category_name, ranged_categories, named_categories)
                    if category_info:
                        new_song['kategoria'] = category_info['name']
                        new_song['kategoriaSkr'] = category_info['abbr']
                piesni_data.append(new_song)
                title_map[tytul_sak] = len(piesni_data) - 1
                songs_added += 1
        else:
            current_sak_category_name = line

    print(f"Zakończono przetwarzanie. Zaktualizowano {songs_updated} pieśni, dodano {songs_added} nowych.")
    print(f"Zapisywanie finalnego wyniku do pliku '{PIESNI_OUTPUT_FILENAME}'...")
    try:
        with open(PIESNI_OUTPUT_FILENAME, 'w', encoding=FILE_ENCODING) as f:
            json.dump(piesni_data, f, indent=JSON_INDENTATION, ensure_ascii=False)
        print(f"Operacja zakończona pomyślnie! Utworzono plik '{PIESNI_OUTPUT_FILENAME}'.")
    except Exception as e:
        print(f"BŁĄD: Wystąpił problem podczas zapisywania pliku wyjściowego: {e}")

if __name__ == "__main__":
    process_and_enrich_songs()