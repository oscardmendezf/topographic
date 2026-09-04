#!/usr/bin/env python3
"""Consolida data/tracklists/*.json en data/canciones.json para el sitio.

Uso:  python3 pipeline/build_tracklists.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "data" / "tracklists"
OUT = ROOT / "data" / "canciones.json"


def main() -> None:
    canciones = {}
    for p in sorted(DIR.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("sin_release") or not d.get("medios"):
            continue
        canciones[d["album_slug"]] = {
            "release_id": d["release_id"],
            "fecha": d.get("fecha"),
            "medios": d["medios"],
        }
    OUT.write_text(json.dumps(canciones, ensure_ascii=False) + "\n", encoding="utf-8")
    pistas = sum(len(m["pistas"]) for c in canciones.values() for m in c["medios"])
    print(f"[canciones] {len(canciones)} álbumes con tracklist, {pistas} pistas")


if __name__ == "__main__":
    main()
