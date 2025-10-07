#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup, Tag


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
}


SEKCJE: List[tuple] = [
    ("ANTYFONA NA WEJŚCIE", "Antyfona na wejście"),
    ("KOLEKTA", "Kolekta"),
    ("MODLITWA NAD DARAMI", "Modlitwa nad darami"),
    ("ANTYFONA NA KOMUNIĘ", "Antyfona na Komunię"),
    ("MODLITWA PO KOMUNII", "Modlitwa po Komunii"),
]


def _normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _text_in_order(el: Tag) -> str:
    """Zwraca tekst elementu, sklejając kolejne węzły tekstowe bez dodawania separatorów.
    Nie dopisujemy nic między <p> a wewnętrznymi <span> (ściśle wg specyfikacji użytkownika).
    """
    try:
        # Używamy .strings aby zachować oryginalne odstępy, bez dodatkowych separatorów
        txt = "".join(list(el.strings))
    except Exception:
        txt = el.get_text(separator="", strip=False)
    return txt.strip()


def _is_albo_paragraph(p: Optional[Tag]) -> bool:
    if p is None or not isinstance(p, Tag):
        return False
    content = _text_in_order(p)
    content = content.lstrip()
    if len(content) < 4:
        return False
    return content[:4].casefold().lower() == "albo"


def _find_header_paragraph(soup: BeautifulSoup, upper_label: str) -> Optional[Tag]:
    """Znajdź <p>, który zawiera <strong><span> o treści dokładnie równej upper_label (po .upper())."""
    for p in soup.find_all("p"):
        strong = p.find("strong")
        if not strong:
            continue
        span = strong.find("span")
        if not span:
            continue
        span_text = _normalize_spaces(span.get_text(strip=True)).upper()
        if span_text == upper_label:
            return p
    return None


def _extract_sigla_from_header(header_p: Tag) -> str:
    """Jeśli w tym samym <p>, obok <strong>, jest jeszcze <span>, pobierz jego treść jako sigla.
    Bierzemy tylko <span> niebędące potomkami <strong>.
    """
    strong = header_p.find("strong")
    if not strong:
        return ""
    sigla_parts: List[str] = []
    for child in header_p.children:
        if isinstance(child, Tag) and child.name == "span" and child not in strong.descendants:
            t = _text_in_order(child)
            t = _normalize_spaces(t)
            if t:
                sigla_parts.append(t)
    return _normalize_spaces(" ".join(sigla_parts)) if sigla_parts else ""


def _extract_section_objects(soup: BeautifulSoup, upper_label: str, title_normal: str) -> List[Dict[str, str]]:
    """Zwraca listę 1-2 obiektów dla danej sekcji (drugi, jeśli występuje wariant po 'Albo')."""
    header_p = _find_header_paragraph(soup, upper_label)
    if not header_p:
        return []

    sigla = _extract_sigla_from_header(header_p)

    # Następny paragraf po nagłówku zawiera treść
    first_content_p = header_p.find_next_sibling("p")
    first_text = _text_in_order(first_content_p) if first_content_p else ""

    items: List[Dict[str, str]] = []
    items.append({
        "tytul": title_normal,
        "sigla": sigla,
        "tekst": first_text,
    })

    # Sprawdzenie wariantu 'Albo' – jeśli kolejny <p> zaczyna się od słowa 'albo',
    # to bierzemy jeszcze następny <p> jako osobny obiekt z sufiksem " 2" w tytule.
    maybe_albo_p = first_content_p.find_next_sibling("p") if first_content_p else None
    if _is_albo_paragraph(maybe_albo_p):
        second_content_p = maybe_albo_p.find_next_sibling("p")
        second_text = _text_in_order(second_content_p) if second_content_p else ""
        items.append({
            "tytul": f"{title_normal} 2",
            "sigla": sigla,
            "tekst": second_text,
        })

    return items


def parse_formularz_from_html(html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    formularz: List[Dict[str, str]] = []
    for upper_label, title_normal in SEKCJE:
        items = _extract_section_objects(soup, upper_label, title_normal)
        formularz.extend(items)
    return formularz


def fetch_html(session: requests.Session, url: str) -> str:
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def find_day_file(base_dir: Path, day_name: str) -> Optional[Path]:
    """Znajdź dokładnie plik o nazwie '{day_name}.json' pod katalogami 'data/' oraz 'Datowane/'."""
    target = f"{day_name}.json"
    for sub in ("data", "Datowane"):
        root = base_dir / sub
        if not root.exists():
            continue
        for r, _dirs, files in os.walk(root):
            if target in files:
                return Path(r) / target
    return None


def load_links(links_path: Path) -> Dict[str, str]:
    with links_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_formularz_to_day_file(day_file: Path, formularz: List[Dict[str, str]]) -> None:
    with day_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["formularz"] = formularz
    with day_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    links_path = base_dir / "linki.json"

    links = load_links(links_path)
    if not isinstance(links, dict):
        print("[BŁĄD] linki.json nie zawiera obiektu klucz->wartość.")
        return

    with requests.Session() as session:
        session.headers.update(HEADERS)

        total = len(links)
        processed = 0
        for idx, (day_name, url) in enumerate(links.items(), start=1):
            print(f"[{idx}/{total}] Dzień: {day_name}")
            if not url:
                print("  - Pomijam (brak URL w linki.json)")
                continue

            day_file = find_day_file(base_dir, day_name)
            if not day_file:
                print("  - [UWAGA] Nie znaleziono pliku dnia dla tej nazwy (data/ ani Datowane/). Pomijam.")
                continue

            try:
                html = fetch_html(session, url)
                formularz = parse_formularz_from_html(html)
                if not formularz:
                    print("  - [UWAGA] Nie znaleziono żadnej z wymaganych sekcji na stronie. Zapiszę pustą listę formularz.")
                write_formularz_to_day_file(day_file, formularz)
                processed += 1
                print(f"  - Zapisano do: {day_file}")
            except requests.RequestException as e:
                print(f"  - [BŁĄD] Problem z pobieraniem: {e}")
            except Exception as e:
                print(f"  - [BŁĄD] Nieoczekiwany błąd: {e}")

        print(f"\nZakończono. Zaktualizowano formularz w {processed} plikach.")


if __name__ == "__main__":
    main()

