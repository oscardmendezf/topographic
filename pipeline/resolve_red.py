#!/usr/bin/env python3
"""Resuelve MBIDs de los nodos de la red que no salen de las membresías del atlas
(productores, arregladores, diseñadores, sellos). Igual que en resolve: búsqueda
por nombre en la API con hints de desambiguación, nada de IDs de memoria.

Escribe data/red_mbids.json y actualiza el frontmatter de content/red/*.md.
Nodos compuestos (varios entes en una ficha) quedan en null a propósito.

Uso:  python3 pipeline/resolve_red.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from musicbrainz import api_get  # reutiliza rate-limit y reintentos

ROOT = Path(__file__).resolve().parent.parent
RED_DIR = ROOT / "content" / "red"
OUT_PATH = ROOT / "data" / "red_mbids.json"

# slug -> (entidad MB, término de búsqueda, hint que debe aparecer en la
# desambiguación o área del candidato). Compuestos: entidad "compuesto".
OBJETIVOS = {
    "eddy-offord": ("artist", "Eddy Offord", None),
    "david-hitchcock": ("artist", "David Hitchcock", "producer"),
    "david-bedford": ("artist", "David Bedford", "composer"),
    "tom-newman": ("artist", "Tom Newman", "producer"),
    "keith-tippett": ("artist", "Keith Tippett", None),
    "roger-dean": ("artist", "Roger Dean", "designer"),
    "dave-stewart": ("artist", "Dave Stewart", "canterbury"),
    "hipgnosis": ("artist", "Hipgnosis", "design"),
    "virgin-records": ("label", "Virgin", "worldwide imprint"),
    "manticore": ("label", "Manticore", None),
    "charisma-tony-stratton-smith": ("compuesto", None, None),
    "advision-trident-abbey-road-the-manor": ("compuesto", None, None),
    "steve-y-john-hackett": ("compuesto", None, None),
}


def buscar(entidad: str, termino: str, hint: str | None) -> dict:
    key = entidad + "s"  # artists / labels
    res = api_get(entidad, {"query": f'{entidad}:"{termino}"', "limit": 8})
    candidatos = res.get(key, [])
    elegido, estado = None, "sin_resultados"
    for c in candidatos:
        texto = " ".join([
            c.get("disambiguation", "") or "",
            (c.get("area") or {}).get("name", "") or "",
            c.get("type", "") or "",
        ]).lower()
        if c.get("name", "").lower() != termino.lower() and termino.lower() not in c.get("name", "").lower():
            continue
        if hint and hint.lower() not in texto:
            continue
        elegido = c
        estado = "ok" if c.get("score", 0) >= 90 else "revisar"
        break
    return {
        "estado": estado,
        "mbid": elegido["id"] if elegido else None,
        "mb_name": elegido.get("name") if elegido else None,
        "disambiguation": (elegido.get("disambiguation") or "") if elegido else None,
        "score": elegido.get("score") if elegido else None,
        "candidatos": [
            {"mbid": c["id"], "name": c.get("name"), "dis": c.get("disambiguation", ""), "score": c.get("score")}
            for c in candidatos[:4]
        ],
    }


def main() -> None:
    resultados = {}
    for slug, (entidad, termino, hint) in OBJETIVOS.items():
        if entidad == "compuesto":
            resultados[slug] = {"estado": "compuesto", "mbid": None}
            print(f"[red] {slug:38s} compuesto (sin MBID único, a propósito)")
            continue
        r = buscar(entidad, termino, hint)
        r["entidad"] = entidad
        resultados[slug] = r
        print(f"[red] {slug:38s} {r['estado']:8s} {r['mbid'] or '—'}  "
              f"{r['mb_name'] or ''}  ({r['disambiguation'] or 'sin desambiguación'})")

    OUT_PATH.write_text(json.dumps(resultados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # actualiza frontmatter de los .md correspondientes
    for slug, r in resultados.items():
        if not r.get("mbid") or r["estado"] != "ok":
            continue
        path = RED_DIR / f"{slug}.md"
        if not path.exists():
            print(f"[red] aviso: no existe {path}")
            continue
        texto = path.read_text(encoding="utf-8")
        campo = "mbid" if r["entidad"] == "artist" else "mb_label_id"
        nuevo = f'{campo}: "{r["mbid"]}"'
        if re.search(r"^mbid: null$", texto, flags=re.M) and campo == "mbid":
            texto = re.sub(r"^mbid: null$", nuevo, texto, count=1, flags=re.M)
        elif f"{campo}:" not in texto:
            texto = texto.replace("\n---\n", f"\n{nuevo}\n---\n", 1)
        path.write_text(texto, encoding="utf-8")
    print("[red] frontmatter actualizado para los resueltos con estado ok")


if __name__ == "__main__":
    main()
