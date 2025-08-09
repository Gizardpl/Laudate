import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class PiesniCorrector:
    def __init__(self, piesni_file_path: str, lekcjonarz_dir: str):
        self.piesni_file_path = piesni_file_path
        self.lekcjonarz_dir = lekcjonarz_dir
        self.lekcjonarz_files = set()
        self.roman_to_arabic = {
            'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
            'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
            'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
            'XVI': '16', 'XVII': '17', 'XVIII': '18', 'XIX': '19', 'XX': '20',
            'XXI': '21', 'XXII': '22', 'XXIII': '23', 'XXIV': '24', 'XXV': '25',
            'XXVI': '26', 'XXVII': '27', 'XXVIII': '28', 'XXIX': '29', 'XXX': '30',
            'XXXI': '31', 'XXXII': '32', 'XXXIII': '33', 'XXXIV': '34'
        }
        
        # Mapowanie duplikatów do poprawnych nazw
        self.duplicate_mapping = {
            # Triduum Paschalne - zachowujemy pierwsze 4 obiekty
            "Msza Wieczerzy Pańskiej": "DELETE",
            "Liturgia Męki Pańskiej": "DELETE", 
            "Wigilia Paschalna": "DELETE",
            "Niedziela Paschy": "DELETE",
            "Niedziela Wielkanocna": "DELETE",
            "Zmartwychwstanie Pańskie": "DELETE",
            "Niedziela Zmartwychwstania Pańskiego": "DELETE",
            
            # Boże Narodzenie
            "Boże Narodzenie": "25_grudnia___Narodzenie_Pańskie",
            "Msza w dzień Bożego Narodzenia": "DELETE",
            
            # Święci
            "Św. Szczepana": "26_grudnia___świętego_Szczepana_pierwszego_męczennika",
            "św. Szczepana": "26_grudnia___świętego_Szczepana_pierwszego_męczennika",
            "Św. Jana ewangelisty": "27_grudnia___świętego_Jana_Apostoła_i_Ewangelisty",
            "Św. Jana Ewangelisty": "27_grudnia___świętego_Jana_Apostoła_i_Ewangelisty",
            
            # Chrystus Król
            "Chrystusa Króla": "Niedziela_Chrystusa_Króla",
            "Uroczystość Chrystusa Króla": "Niedziela_Chrystusa_Króla",
            "Chrytusa Króla": "Niedziela_Chrystusa_Króla",
            
            # Trójca Święta
            "Niedziela Trójcy Świętej": "Niedziela_Trójcy_Świętej",
            "Uroczystość Trójcy Świętej": "Niedziela_Trójcy_Świętej",
            "Najświętszej Trójcy": "Niedziela_Trójcy_Świętej",
            "Uroczystość Najświętszej Trójcy": "Niedziela_Trójcy_Świętej",
            "Trójcy Prznejaświętszej": "Niedziela_Trójcy_Świętej",
            "Trójcy Przenajświętszej": "Niedziela_Trójcy_Świętej",
            "Uroczystość Trójcy Przenajświętszej": "Niedziela_Trójcy_Świętej",
            
            # Święta Rodzina
            "Świętej Rodziny": "Niedziela_w_oktawie_Narodzenia_Pańskiego___Święto_Świętej_Rodziny",
            
            # Objawienie Pańskie
            "6 stycznia": "6_stycznia___Objawienie_Pańskie",
            
            # Ofiarowanie Pańskie
            "2 luty": "2_lutego___Ofiarowanie_Pańskie",
            "2 lutego": "2_lutego___Ofiarowanie_Pańskie",
            
            # Święci z datami
            "25 stycznia": "25_stycznia___Nawrócenie_świętego_Pawła_Apostoła",
            "19 marca": "19_marca___świętego_Józefa_Oblubieńca_NMP",
            "św. Józefa": "19_marca___świętego_Józefa_Oblubieńca_NMP",
            "św. Józefa Robotnika": "1_maja___świętego_Józefa_Robotnika",
            "3 maja": "3_maja___świętych_Apostołów_Filipa_i_Jakuba",
            "24 czerwca": "24_czerwca___Narodzenie_świętego_Jana_Chrzciciela",
            "29 czerwca": "29_czerwca___świętych_Apostołów_Piotra_i_Pawła",
            "15 sierpnia": "15_sierpnia___Wniebowzięcie_NMP",
            "8 września": "8_września___Narodzenie_NMP",
            "1 listopada": "1_listopada___Wszystkich_Świętych",
            "2 listopada": "2_listopada___Wspomnienie_wszystkich_wiernych_zmarłych",
            "8 grudnia": "8_grudnia___Niepokalane_Poczęcie_NMP",
            
            # Usuwanie niepoprawnych obiektów
            "Propozycje śpiewów": "DELETE",
            "Propozycje  śpiewów": "DELETE",
        }
        
    def load_lekcjonarz_files(self):
        """Ładuje wszystkie nazwy plików z folderu Lekcjonarz_JSON"""
        for root, dirs, files in os.walk(self.lekcjonarz_dir):
            for file in files:
                if file.endswith('.json'):
                    # Usuwamy rozszerzenie .json
                    filename = file[:-5]
                    self.lekcjonarz_files.add(filename)
        print(f"Załadowano {len(self.lekcjonarz_files)} plików z Lekcjonarz_JSON")
    
    def roman_to_arabic_convert(self, text: str) -> str:
        """Konwertuje cyfry rzymskie na arabskie"""
        for roman, arabic in self.roman_to_arabic.items():
            # Zastępujemy cyfry rzymskie na początku słowa lub po spacji
            pattern = r'\b' + roman + r'\b'
            text = re.sub(pattern, arabic, text)
        return text
    
    def clean_name(self, name: str) -> str:
        """Czyści nazwę z niepotrzebnych elementów"""
        # Usuwamy "Propozycje śpiewów", lata, itp.
        name = re.sub(r'Propozycje\s+śpiewów?\s*-?\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'Propozycje\s+spiewów?\s*-?\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'Propozycje\s+śpewów?\s*-?\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*-\s*', ' ', name)
        name = re.sub(r'\(\d{4}\)', '', name)  # Usuwamy lata w nawiasach
        name = re.sub(r'\s+\d{4}\s*', ' ', name)  # Usuwamy lata
        name = re.sub(r'\(archiwalne\)', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\([ABC]\)', '', name)  # Usuwamy oznaczenia lat liturgicznych
        
        # Konwertujemy cyfry rzymskie na arabskie
        name = self.roman_to_arabic_convert(name)
        
        # Poprawiamy format niedziel w okresach liturgicznych
        name = re.sub(r'(\d+)\s+Niedziela\s+w\s+Wielkim\s+Poście', r'\1 Niedziela Wielkiego Postu', name)
        name = re.sub(r'(\d+)\s+Niedziela\s+w\s+Poście', r'\1 Niedziela Wielkiego Postu', name)
        name = re.sub(r'(\d+)\s+Niedziela\s+w\s+Adwencie', r'\1 Niedziela Adwentu', name)
        
        # Czyścimy wielokrotne spacje
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def find_matching_lekcjonarz_file(self, cleaned_name: str) -> str:
        """Znajduje odpowiadający plik w Lekcjonarz_JSON"""
        # Próbujemy znaleźć dokładne dopasowanie
        if cleaned_name in self.lekcjonarz_files:
            return cleaned_name
            
        # Próbujemy znaleźć podobne nazwy
        cleaned_lower = cleaned_name.lower().replace(' ', '_')
        for lekcjonarz_file in self.lekcjonarz_files:
            if lekcjonarz_file.lower().replace(' ', '_') == cleaned_lower:
                return lekcjonarz_file
                
        # Próbujemy znaleźć częściowe dopasowania
        for lekcjonarz_file in self.lekcjonarz_files:
            if cleaned_name.lower() in lekcjonarz_file.lower() or lekcjonarz_file.lower() in cleaned_name.lower():
                return lekcjonarz_file
                
        return cleaned_name
    
    def process_piesni_file(self):
        """Przetwarza plik pieśni i usuwa duplikaty"""
        with open(self.piesni_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Załadowano {len(data)} obiektów z pliku pieśni")
        
        # Zachowujemy pierwsze 4 obiekty bez zmian (Triduum Paschalne)
        preserved_objects = data[:4]
        remaining_objects = data[4:]
        
        # Grupujemy obiekty według oczyszczonych nazw
        name_groups = defaultdict(list)
        processed_objects = []
        
        for obj in remaining_objects:
            original_name = obj['nazwa']
            
            # Sprawdzamy czy obiekt ma być usunięty
            if original_name in self.duplicate_mapping:
                if self.duplicate_mapping[original_name] == "DELETE":
                    print(f"Usuwam duplikat: {original_name}")
                    continue
                else:
                    # Mapujemy na poprawną nazwę
                    target_name = self.duplicate_mapping[original_name]
                    if target_name in self.lekcjonarz_files:
                        obj['nazwa'] = target_name
                        processed_objects.append(obj)
                        print(f"Mapuję: {original_name} -> {target_name}")
                        continue
            
            # Czyścimy nazwę
            cleaned_name = self.clean_name(original_name)
            
            # Sprawdzamy czy nazwa nie jest pusta lub niepoprawna
            if not cleaned_name or cleaned_name.lower() in ['propozycje śpiewów', 'propozycje spiewów']:
                print(f"Usuwam niepoprawny obiekt: {original_name}")
                continue
            
            # Znajdujemy odpowiadający plik w Lekcjonarz_JSON
            matching_file = self.find_matching_lekcjonarz_file(cleaned_name)
            
            obj['nazwa'] = matching_file
            name_groups[matching_file].append(obj)
        
        # Dla każdej grupy zachowujemy tylko jeden obiekt (pierwszy)
        for group_name, objects in name_groups.items():
            if len(objects) > 1:
                print(f"Znaleziono {len(objects)} duplikatów dla: {group_name}")
                # Wybieramy obiekt bez roku w linku (jeśli istnieje)
                best_object = objects[0]
                for obj in objects:
                    if not re.search(r'\d{4}', obj['link']):
                        best_object = obj
                        break
                processed_objects.append(best_object)
            else:
                processed_objects.append(objects[0])
        
        # Łączymy zachowane obiekty z przetworzonymi
        final_objects = preserved_objects + processed_objects
        
        print(f"Końcowy wynik: {len(final_objects)} obiektów (było {len(data)})")
        print(f"Usunięto {len(data) - len(final_objects)} duplikatów/niepoprawnych obiektów")
        
        return final_objects
    
    def save_corrected_file(self, corrected_data: List[Dict]):
        """Zapisuje poprawiony plik"""
        backup_path = self.piesni_file_path + '.backup'
        
        # Tworzymy kopię zapasową
        with open(self.piesni_file_path, 'r', encoding='utf-8') as f:
            original_data = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_data)
        print(f"Utworzono kopię zapasową: {backup_path}")
        
        # Zapisujemy poprawiony plik
        with open(self.piesni_file_path, 'w', encoding='utf-8') as f:
            json.dump(corrected_data, f, ensure_ascii=False, indent=4)
        print(f"Zapisano poprawiony plik: {self.piesni_file_path}")

def main():
    piesni_file = r"c:\Users\blzej\Desktop\Aplikacja dla studenta\skrypt\piesni_podloga_linki.json"
    lekcjonarz_dir = r"c:\Users\blzej\Desktop\Aplikacja dla studenta\skrypt\Lekcjonarz_JSON"
    
    corrector = PiesniCorrector(piesni_file, lekcjonarz_dir)
    
    print("=== KOREKTA PLIKU PIEŚNI ===")
    print("1. Ładowanie plików z Lekcjonarz_JSON...")
    corrector.load_lekcjonarz_files()
    
    print("\n2. Przetwarzanie pliku pieśni...")
    corrected_data = corrector.process_piesni_file()
    
    print("\n3. Zapisywanie poprawionego pliku...")
    corrector.save_corrected_file(corrected_data)
    
    print("\n=== KOREKTA ZAKOŃCZONA ===")

if __name__ == "__main__":
    main()
