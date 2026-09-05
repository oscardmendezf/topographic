#!/usr/bin/env python3
"""Aplica las historias redactadas (data/editorial_historias/*.json) al cuerpo de
cada ficha de álbum. Conserva el análisis breve como entrada y añade, tras el
marcador `<!-- historia:editorial -->`, las secciones largas (historia,
producción, recepción). Re-ejecutar reemplaza la historia anterior sin tocar el
análisis ni el frontmatter (salvo el campo `historia`).

Lint (sale ≠0): posiciones de chart, cifras de ventas, certificaciones y fechas
completas escritas en la historia — regla del brief: ningún dato duro de memoria.

Uso:  python3 pipeline/merge_historias.py [--check]
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge_editorial_f2 import RE_CHART, poner_campo

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "albumes"
DIR = ROOT / "data" / "editorial_historias"
MARCA = "<!-- historia:editorial -->"

RE_DURO = re.compile(
    r"\b(?:puesto|posici[oó]n|n[úu]mero|lugar)\s+(?:n[ºo°]?\s*)?\d+\b"
    r"|\bdisco de (?:oro|platino)\b|\bcertific"
    r"|\b\d[\d.,]*\s*(?:millones|mill[oó]n)\s+de\s+(?:copias|discos|ejemplares|unidades)"
    r"|\b\d{1,3}(?:\.\d{3})+\s+(?:copias|discos|ejemplares|unidades)"
    r"|\b\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{4}",
    re.I,
)
SECCIONES = ("## La historia", "## La producción", "## Recepción y legado")


def main() -> None:
    check = "--check" in sys.argv
    n, lint, faltan, cortos = 0, [], [], []
    archivos = sorted(DIR.glob("*.json")) + sorted(DIR.glob("partes/*/*.json"))
    for jpath in archivos:
        data = json.loads(jpath.read_text(encoding="utf-8"))
        # Formato por grupo {"albumes": [...]} o por álbum {"album_slug", "historia_md"}.
        items = data["albumes"] if "albumes" in data else [data]
        for a in items:
            slug = a["album_slug"]
            path = CONTENT / f"{slug}.md"
            if not path.exists():
                faltan.append(f"{jpath.stem}: {slug}")
                continue
            historia = (a.get("historia_md") or "").strip()
            if not historia:
                faltan.append(f"{jpath.stem}: {slug} (vacío)")
                continue
            malo = False
            for rx in (RE_CHART, RE_DURO):
                m = rx.search(historia)
                if m:
                    lint.append(f"{slug}: «{m.group(0)}»")
                    malo = True
            if len(historia.split()) < 220:
                cortos.append(f"{slug}: {len(historia.split())} palabras")
            for s in SECCIONES:
                if s not in historia:
                    lint.append(f"{slug}: falta sección «{s}»")
                    malo = True
            if malo:
                continue  # no se aplica una historia que no pasa el lint
            if check:
                n += 1
                continue
            txt = path.read_text(encoding="utf-8")
            m = re.match(r"^---\n(.*?\n)---\n(.*)$", txt, re.S)
            fm, cuerpo = m.group(1), m.group(2)
            analisis = cuerpo.split(MARCA)[0].strip()
            # Limpia el campo que una versión anterior dejó fuera del frontmatter.
            analisis = re.sub(r'^historia: "editorial"\s*', "", analisis).strip()
            fm = poner_campo(fm, "historia", "editorial")
            path.write_text(f"---\n{fm}---\n\n{analisis}\n\n{MARCA}\n\n{historia}\n", encoding="utf-8")
            n += 1
    print(f"[historias] {'verificadas' if check else 'aplicadas'}: {n} · sin ficha: {len(faltan)} · cortas: {len(cortos)}")
    for s in faltan + cortos:
        print("   ", s)
    if lint:
        print(f"[historias] LINT ({len(lint)}):")
        for s in lint:
            print("   ", s)
        sys.exit(1)


if __name__ == "__main__":
    main()
