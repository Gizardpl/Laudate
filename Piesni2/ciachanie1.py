import os
from pypdf import PdfReader, PdfWriter

# --- Konfiguracja ---
# Ścieżka do wejściowego pliku PDF, który chcesz podzielić
input_pdf_path = "SAK.pdf" 
# Nazwa dla wyjściowego pliku PDF z podzielonymi stronami
output_pdf_path = "SAK2.pdf"
# --- Koniec Konfiguracji ---

def split_pdf_vertically_robust(input_path, output_path):
    """
    Dzieli każdą stronę w danym pliku PDF pionowo na dwie równe części.
    Ta wersja używa bardziej niezawodnej metody transformacji, kompatybilnej
    ze starszymi wersjami biblioteki pypdf.

    Args:
        input_path (str): Ścieżka do wejściowego pliku PDF.
        output_path (str): Ścieżka do zapisu wynikowego pliku PDF.
    """
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        # Pętla przez wszystkie strony w oryginalnym pliku
        for page in reader.pages:
            original_width = page.mediabox.width
            original_height = page.mediabox.height
            
            # Szerokość każdej z nowych stron-połówek
            new_width = original_width / 2

            # --- Tworzenie LEWEJ połówki ---
            left_half = writer.add_blank_page(width=new_width, height=original_height)
            # Używamy funkcji merge_transformed_page, która od razu nakłada
            # oryginalną stronę bez przesunięcia (transformacja "zerowa").
            # [1, 0, 0, 1, 0, 0] to macierz identyczności.
            left_half.merge_transformed_page(page, [1, 0, 0, 1, 0, 0])

            # --- Tworzenie PRAWEJ połówki ---
            right_half = writer.add_blank_page(width=new_width, height=original_height)
            
            # Używamy tej samej funkcji, ale tym razem podajemy macierz transformacji,
            # która przesuwa treść w lewo (tx = -new_width).
            # To jest najbardziej niezawodny sposób na przesunięcie treści.
            # Macierz transformacji: [a, b, c, d, tx, ty]
            right_half.merge_transformed_page(page, [1, 0, 0, 1, -new_width, 0])

        # Zapisanie nowego pliku PDF na dysku
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
            
        print(f"Sukces! Plik został poprawnie podzielony i zapisany jako: {output_path}")

    except FileNotFoundError:
        print(f"BŁĄD: Plik wejściowy nie został znaleziony pod ścieżką: {input_path}")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")

# Ta część uruchamia funkcję, gdy skrypt jest wykonywany bezpośrednio
if __name__ == "__main__":
    if os.path.exists(input_pdf_path):
        split_pdf_vertically_robust(input_pdf_path, output_pdf_path)
    else:
        print(f"Plik '{input_pdf_path}' nie istnieje. Proszę zaktualizować zmienną 'input_pdf_path' na górze skryptu.")