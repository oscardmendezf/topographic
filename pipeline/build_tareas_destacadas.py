#!/usr/bin/env python3
"""Manifiestos para elegir las canciones destacadas de cada álbum.

Un juicio por álbum (no por canción): el redactor elige de 1 a 3 piezas clave
del tracklist verificado y les pone estrellas y una frase. Las demás quedan sin
nota, igual que los charts sin fuente. Son ~1300 decisiones, no 13.534.

El manifiesto trae el tracklist con los números de pista (el ancla dura: el
redactor solo puede elegir números que existen) y los metadatos del álbum. El
texto de la ficha NO se copia acá: el redactor abre content/albumes/<slug>.md.

Uso:  python3 pipeline/build_tareas_destacadas.py [--lote N] [--prefijo dest]
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ALBUMES = ROOT / "content" / "albumes"


def campo(fm: str, k: str):
    m = re.search(rf'^{k}:\s*"?([^"\n]*)"?\s*$', fm, re.M)
    v = m.group(1).strip() if m else None
    return v if v and v != "null" else None


def main() -> None:
    lote = int(sys.argv[sys.argv.index("--lote") + 1]) if "--lote" in sys.argv else 40
    prefijo = sys.argv[sys.argv.index("--prefijo") + 1] if "--prefijo" in sys.argv else "dest"
    canciones = json.loads((DATA / "canciones.json").read_text(encoding="utf-8"))

    items, sin_lista = [], 0
    for md in sorted(ALBUMES.glob("*.md")):
        lista = canciones.get(md.stem)
        if not lista:
            sin_lista += 1
            continue
        fm = md.read_text(encoding="utf-8").split("---\n", 2)[1]
        # `medio` es obligatorio: en los 94 álbumes de más de un disco los números
        # de pista se repiten entre medios, así que (medio, n) es la clave real.
        pistas = [{"medio": i, "n": p["n"], "titulo": p["titulo"], "ms": p["ms"]}
                  for i, m in enumerate(lista["medios"], 1) for p in m["pistas"]]
        items.append({
            "album_slug": md.stem,
            "titulo": campo(fm, "titulo"),
            "artista": campo(fm, "artista"),
            "artista_slug": campo(fm, "artista_slug"),
            "anio": int(campo(fm, "anio_ficha") or 0),
            "escena": campo(fm, "escena"),
            "estrellas_critica_album": campo(fm, "estrellas_critica"),
            "ficha": f"content/albumes/{md.stem}.md",
            "medios": len(lista["medios"]),
            "tracklist": pistas,
        })

    out_dir = DATA / f"tareas_{prefijo}"
    out_dir.mkdir(exist_ok=True)
    for viejo in out_dir.glob(f"{prefijo}-*.json"):
        viejo.unlink()
    grupos = []
    for i in range(0, len(items), lote):
        gid = f"{prefijo}-{i // lote + 1:02d}"
        g = {"id": gid, "albumes": items[i:i + lote]}
        (out_dir / f"{gid}.json").write_text(json.dumps(g, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        grupos.append({"id": gid, "n": len(g["albumes"]),
                       "desde": g["albumes"][0]["album_slug"], "hasta": g["albumes"][-1]["album_slug"]})
    (DATA / f"tareas_{prefijo}.json").write_text(
        json.dumps({"grupos": grupos}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    pistas = sum(len(i["tracklist"]) for i in items)
    print(f"[destacadas] {len(items)} álbumes ({pistas} pistas) en {len(grupos)} grupos de ≤{lote}"
          f" → data/tareas_{prefijo}/")
    if sin_lista:
        print(f"[destacadas] {sin_lista} fichas sin tracklist en MusicBrainz, quedan fuera")


if __name__ == "__main__":
    main()
