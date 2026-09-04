#!/usr/bin/env python3
"""Listas de canciones desde MusicBrainz, una por álbum.

Criterio editorial: la edición OFICIAL MÁS TEMPRANA de cada release-group —
la lista canónica de época, sin bonus tracks de reediciones.

Para cada ficha (content/albumes/*.md con mb_rgid):
  1. lista los releases del RG y elige el más temprano oficial
  2. baja ese release con inc=recordings (medios y pistas)
  3. guarda data/tracklists/<slug>.json (reanudable)

Uso:  python3 pipeline/fetch_tracklists.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from musicbrainz import api_get

ROOT = Path(__file__).resolve().parent.parent
ALBUMES = ROOT / "content" / "albumes"
OUT = ROOT / "data" / "tracklists"


def elegir_release(rgid: str) -> dict | None:
    res = api_get("release", {"release-group": rgid, "limit": 100})
    releases = res.get("releases", [])
    if not releases:
        return None

    def clave(r):
        oficial = 0 if (r.get("status") or "Official") == "Official" else 1
        fecha = r.get("date") or "9999"
        return (oficial, len(fecha) < 4, fecha)

    return sorted(releases, key=clave)[0]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hechos = {p.stem for p in OUT.glob("*.json")}
    pendientes = []
    for p in sorted(ALBUMES.glob("*.md")):
        if p.stem in hechos:
            continue
        m = re.search(r'^mb_rgid: "([a-f0-9-]+)"$', p.read_text(encoding="utf-8"), flags=re.M)
        if m:
            pendientes.append((p.stem, m.group(1)))
    print(f"[canciones] pendientes: {len(pendientes)}", flush=True)

    for i, (slug, rgid) in enumerate(pendientes, 1):
        try:
            rel = elegir_release(rgid)
            if not rel:
                (OUT / f"{slug}.json").write_text('{"sin_release": true}\n', encoding="utf-8")
                continue
            det = api_get(f"release/{rel['id']}", {"inc": "recordings"})
            medios = []
            for med in det.get("media", []):
                pistas = [{
                    "n": t.get("position"),
                    "titulo": t.get("title"),
                    "ms": t.get("length"),
                } for t in med.get("tracks", [])]
                if pistas:
                    medios.append({
                        "formato": med.get("format"),
                        "titulo": med.get("title") or None,
                        "pistas": pistas,
                    })
            (OUT / f"{slug}.json").write_text(json.dumps({
                "album_slug": slug, "release_id": rel["id"],
                "fecha": rel.get("date"), "pais": rel.get("country"),
                "medios": medios,
            }, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            print(f"[canciones] ERROR {slug}: {e}", flush=True)
        if i % 100 == 0:
            print(f"[canciones] {i}/{len(pendientes)}", flush=True)
    print("[canciones] listo", flush=True)


if __name__ == "__main__":
    main()
