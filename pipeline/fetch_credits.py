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


def main() -> None:
    """v2: browse de TODOS los releases del RG con rels incluidos (1 request,
    paginado si >100) y unión de créditos entre ediciones — los créditos de
    MB suelen estar colgados en una edición cualquiera, no en la primera."""
    OUT.mkdir(parents=True, exist_ok=True)
    fichas = sorted(ALBUMES.glob("*.md"))
    hechos = {p.stem for p in OUT.glob("*.json")
              if json.loads((OUT / p.name).read_text(encoding="utf-8")).get("v") == 2}
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
            releases, offset = [], 0
            while True:
                page = api_get("release", {
                    "release-group": rgid, "limit": 100, "offset": offset,
                    "inc": "artist-rels+place-rels+labels",
                })
                releases.extend(page.get("releases", []))
                total = page.get("release-count", len(releases))
                offset += 100
                if len(releases) >= total:
                    break
            labels, rels, vistos_l, vistos_r = [], [], set(), set()
            fecha = None
            for rel in sorted(releases, key=lambda r: (r.get("date") or "9999")):
                fecha = fecha or rel.get("date")
                for li in rel.get("label-info", []):
                    lab = li.get("label") or {}
                    if lab.get("id") and lab["id"] not in vistos_l:
                        vistos_l.add(lab["id"])
                        labels.append({"nombre": lab.get("name"), "mbid": lab["id"]})
                for r in rel.get("relations", []):
                    if r.get("target-type") not in ("artist", "place"):
                        continue
                    ent = r.get("artist") or r.get("place") or {}
                    clave = (ent.get("id"), r.get("type"))
                    if not ent.get("id") or clave in vistos_r:
                        continue
                    vistos_r.add(clave)
                    rels.append({
                        "tipo": r.get("type"), "target": r.get("target-type"),
                        "nombre": ent.get("name"), "mbid": ent["id"],
                        "atributos": r.get("attributes", []),
                    })
            (OUT / f"{slug}.json").write_text(json.dumps({
                "v": 2, "album_slug": slug, "rgid": rgid,
                "n_releases": len(releases), "release_fecha": fecha,
                "labels": labels, "rels": rels,
            }, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception as e:  # noqa: BLE001 — no frenar 900 álbumes por uno
            print(f"[creditos] ERROR {slug}: {e}", flush=True)
        if i % 50 == 0:
            print(f"[creditos] {i}/{len(pendientes)}", flush=True)
    print("[creditos] listo", flush=True)


if __name__ == "__main__":
    main()
