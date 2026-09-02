#!/usr/bin/env python3
"""Créditos a nivel release desde MusicBrainz, para verificar la red.

Para cada ficha de álbum (content/albumes/*.md con mb_rgid):
  1. lista los releases del release-group y elige el más temprano oficial
  2. baja ese release con artist-rels (productor, ingeniero, arte), place-rels
     (estudios) y labels (sellos)
  3. guarda data/raw_credits/<album_slug>.json (reanudable)

Uso:  python3 pipeline/fetch_credits.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from musicbrainz import api_get

ROOT = Path(__file__).resolve().parent.parent
ALBUMES = ROOT / "content" / "albumes"
OUT = ROOT / "data" / "raw_credits"


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
    fichas = sorted(ALBUMES.glob("*.md"))
    hechos = {p.stem for p in OUT.glob("*.json")}
    pendientes = []
    for p in fichas:
        if p.stem in hechos:
            continue
        m = re.search(r'^mb_rgid: "([a-f0-9-]+)"$', p.read_text(encoding="utf-8"), flags=re.M)
        if m:
            pendientes.append((p.stem, m.group(1)))
    print(f"[creditos] pendientes: {len(pendientes)} de {len(fichas)}", flush=True)

    for i, (slug, rgid) in enumerate(pendientes, 1):
        try:
            rel = elegir_release(rgid)
            if not rel:
                (OUT / f"{slug}.json").write_text('{"sin_release": true}\n', encoding="utf-8")
                continue
            det = api_get(f"release/{rel['id']}", {"inc": "artist-rels+place-rels+labels"})
            out = {
                "album_slug": slug,
                "rgid": rgid,
                "release_id": rel["id"],
                "release_fecha": rel.get("date"),
                "release_pais": rel.get("country"),
                "labels": [
                    {"nombre": (li.get("label") or {}).get("name"),
                     "mbid": (li.get("label") or {}).get("id")}
                    for li in det.get("label-info", []) if li.get("label")
                ],
                "rels": [
                    {
                        "tipo": r.get("type"),
                        "target": r.get("target-type"),
                        "nombre": (r.get("artist") or r.get("place") or {}).get("name"),
                        "mbid": (r.get("artist") or r.get("place") or {}).get("id"),
                        "atributos": r.get("attributes", []),
                    }
                    for r in det.get("relations", [])
                    if r.get("target-type") in ("artist", "place")
                ],
            }
            (OUT / f"{slug}.json").write_text(json.dumps(out, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception as e:  # noqa: BLE001 — no frenar 900 álbumes por uno
            print(f"[creditos] ERROR {slug}: {e}", flush=True)
        if i % 50 == 0:
            print(f"[creditos] {i}/{len(pendientes)}", flush=True)
    print("[creditos] listo", flush=True)


if __name__ == "__main__":
    main()
