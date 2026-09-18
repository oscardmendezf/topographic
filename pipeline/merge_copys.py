#!/usr/bin/env python3
"""Aplica las fichas largas de artista redactadas (data/editorial_copys/**.json)
al cuerpo de content/artistas/<slug>.md.

Conserva la entradilla del prototipo como entrada y añade, tras el marcador
`<!-- copy:editorial -->`, la ficha larga. Re-ejecutar reemplaza la ficha sin
tocar la entradilla ni el frontmatter (salvo el campo `copy`).

Lint (sale ≠0 y no aplica esa ficha): posiciones de chart, ventas,
certificaciones, fechas completas, títulos markdown y fichas fuera de rango.

Uso:  python3 pipeline/merge_copys.py [--check]
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge_editorial_f2 import RE_CHART, poner_campo
from merge_historias import RE_DURO

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "artistas"
DIR = ROOT / "data" / "editorial_copys"
MARCA = "<!-- copy:editorial -->"
MIN_PALABRAS, MAX_PALABRAS = 280, 520


def main() -> None:
    check = "--check" in sys.argv
    n, lint, faltan, avisos = 0, [], [], []
    archivos = sorted(DIR.glob("*.json")) + sorted(DIR.glob("partes/*/*.json"))
    for jpath in archivos:
        data = json.loads(jpath.read_text(encoding="utf-8"))
        items = data["artistas"] if "artistas" in data else [data]
        for a in items:
            slug = a["slug"]
            path = CONTENT / f"{slug}.md"
            if not path.exists():
                faltan.append(f"{jpath.stem}: {slug}")
                continue
            copy = (a.get("copy_md") or "").strip()
            if not copy:
                faltan.append(f"{jpath.stem}: {slug} (vacío)")
                continue
            malo = False
            for rx in (RE_CHART, RE_DURO):
                m = rx.search(copy)
                if m:
                    lint.append(f"{slug}: dato duro «{m.group(0)}»")
                    malo = True
            if re.search(r"^#{1,6}\s", copy, re.M):
                lint.append(f"{slug}: la ficha de artista va sin títulos")
                malo = True
            pal = len(copy.split())
            if not (MIN_PALABRAS <= pal <= MAX_PALABRAS):
                avisos.append(f"{slug}: {pal} palabras (rango {MIN_PALABRAS}–{MAX_PALABRAS})")
                if pal < 200:
                    lint.append(f"{slug}: ficha demasiado corta ({pal} palabras)")
                    malo = True
            if len([p for p in copy.split("\n\n") if p.strip()]) < 3:
                avisos.append(f"{slug}: menos de 3 párrafos")
            if malo:
                continue
            if check:
                n += 1
                continue
            txt = path.read_text(encoding="utf-8")
            m = re.match(r"^---\n(.*?\n)---\n(.*)$", txt, re.S)
            fm, cuerpo = m.group(1), m.group(2)
            entradilla = cuerpo.split(MARCA)[0].strip()
            fm = poner_campo(fm, "copy", "editorial")
            path.write_text(f"---\n{fm}---\n\n{entradilla}\n\n{MARCA}\n\n{copy}\n", encoding="utf-8")
            n += 1
    print(f"[copys] {'verificadas' if check else 'aplicadas'}: {n} · sin ficha: {len(faltan)} · avisos: {len(avisos)}")
    for s in faltan + avisos:
        print("   ", s)
    if lint:
        print(f"[copys] LINT ({len(lint)}):")
        for s in lint:
            print("   ", s)
        sys.exit(1)


if __name__ == "__main__":
    main()
