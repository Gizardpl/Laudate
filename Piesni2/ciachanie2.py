import os
from pypdf import PdfReader, PdfWriter

# --- Konfiguracja ---
# Ścieżka do wejściowego pliku PDF
input_pdf_path = "SAK2.pdf" 
# Nazwa dla wyjściowego pliku PDF bez stopki
output_pdf_path = "SAK3.pdf"
# Liczba pikseli do odcięcia Z DOŁU każdej strony
pixels_to_remove_from_bottom = 185
# --- Koniec Konfiguracji ---

def crop_pdf_bottom(input_path, output_path, crop_amount):
    """
    Tworzy nowy plik PDF, przycinając dolną część każdej strony o zadaną wartość.

    Args:
        input_path (str): Ścieżka do wejściowego pliku PDF.
        output_path (str): Ścieżka do zapisu wynikowego pliku PDF.
        crop_amount (int): Wysokość w pikselach do odcięcia z dołu strony.
    """
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        # Pętla przez wszystkie strony w oryginalnym pliku
        for page in reader.pages:
            # Pobranie oryginalnych wymiarów strony
            original_width = page.mediabox.width
            original_height = page.mediabox.height
            
            # Sprawdzenie, czy strona nie jest zbyt niska do przycięcia
            if original_height <= crop_amount:
                print(f"Ostrzeżenie: Strona jest zbyt niska, aby ją przyciąć. Zostaje skopiowana bez zmian.")
                writer.add_page(page)
                continue

            # NAJWAŻNIEJSZY KROK: Modyfikacja "pudełek" definiujących stronę
            # Współrzędne w PDF liczone są od lewego dolnego rogu (0, 0).
            
            # 1. Modyfikujemy CropBox (widoczny obszar):
            # Przesuwamy dolną krawędź w górę o zadaną wartość.
            page.cropbox.lower_left = (0, crop_amount)
            # Górna krawędź pozostaje bez zmian.
            page.cropbox.upper_right = (original_width, original_height)
            
            # 2. Synchronizujemy MediaBox (fizyczne granice strony) z CropBox.
            # Jest to kluczowe dla zapewnienia kompatybilności z różnymi przeglądarkami PDF.
            page.mediabox = page.cropbox
            
            # Dodajemy zmodyfikowaną (przyciętą) stronę do nowego pliku
            writer.add_page(page)

        # Zapisanie nowego pliku PDF na dysku
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
            
        print(f"Sukces! Stopka została usunięta, a plik zapisano jako: {output_path}")

    except FileNotFoundError:
        print(f"BŁĄD: Plik wejściowy nie został znaleziony pod ścieżką: {input_path}")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")

# Ta część uruchamia funkcję, gdy skrypt jest wykonywany bezpośrednio
if __name__ == "__main__":
    if os.path.exists(input_pdf_path):
        crop_pdf_bottom(input_pdf_path, output_pdf_path, pixels_to_remove_from_bottom)
    else:
        print(f"Plik '{input_pdf_path}' nie istnieje. Proszę zaktualizować zmienną 'input_pdf_path' na górze skryptu.")