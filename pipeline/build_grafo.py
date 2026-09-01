#!/usr/bin/env python3
"""Atlas del Prog — Fase 1, punto 3: data/grafo.json para el grafo navegable.

Nodos: los 29 artistas del atlas + los 20 nodos de la red (content/red/*.md).
Aristas:
  - member_of derivadas de MusicBrainz (estado 'musicbrainz'), solo para las
    personas de la red cuyo mbid coincide con una membresía del atlas.
  - las conexiones curadas de pipeline/red_edges.json (estado 'prototipo').

Formato: elementos Cytoscape.js ({data: {...}}).

Uso:  python3 pipeline/build_grafo.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATLAS_PATH = ROOT / "data" / "atlas.json"
RED_DIR = ROOT / "content" / "red"
EDGES_PATH = ROOT / "pipeline" / "red_edges.json"
OUT_PATH = ROOT / "data" / "grafo.json"

ETIQUETA_TIPO = {
    "member_of": "miembro de",
    "produced": "produjo a",
    "engineered": "ingeniería para",
    "arranged": "arregló para",
    "guested_on": "invitado de",
    "designed_artwork": "diseñó para",
    "signed_to": "fichó a",
    "recorded_at": "grabó en",
    "wrote_lyrics": "letras para",
}


def leer_frontmatter(path: Path) -> dict:
    texto = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", texto, flags=re.S)
    out = {}
    if m:
        for linea in m.group(1).splitlines():
            k, _, v = linea.partition(":")
            v = v.strip()
            out[k.strip()] = None if v == "null" else json.loads(v) if v.startswith('"') else v
    return out


def main() -> None:
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    curadas = json.loads(EDGES_PATH.read_text(encoding="utf-8"))["aristas"]
    slugs_artistas = set()

    nodes, edges = [], []
    for a in atlas["nodos"]["artistas"]:
        slugs_artistas.add(a["slug"])
        nodes.append({"data": {
            "id": f"a:{a['slug']}",
            "slug": a["slug"],
            "label": a["nombre"],
            "tipo": "artista",
            "grupo": a["grupo"],
        }})

    red_por_mbid = {}
    for md in sorted(RED_DIR.glob("*.md")):
        fm = leer_frontmatter(md)
        if fm.get("tipo") != "red":
            continue
        nodes.append({"data": {
            "id": f"r:{fm['slug']}",
            "slug": fm["slug"],
            "label": fm["nombre"],
            "tipo": fm["tipo_nodo"],
            "rol": fm.get("rol"),
        }})
        if fm.get("mbid"):
            red_por_mbid[fm["mbid"]] = fm["slug"]

    # membresías verificadas (MusicBrainz) de las personas de la red
    vistos = set()
    for m in atlas["aristas"]["member_of"]:
        rslug = red_por_mbid.get(m["person_mbid"])
        if not rslug or m["artist_slug"] not in slugs_artistas:
            continue
        clave = (rslug, m["artist_slug"], "member_of")
        if clave in vistos:  # etapas repetidas (p. ej. Collins x2) -> una arista
            continue
        vistos.add(clave)
        rango = f"{m['desde'] or '¿?'}–{m['hasta'] or ('act.' if m['vigente'] else '¿?')}"
        edges.append({"data": {
            "id": f"e:{rslug}:{m['artist_slug']}:member_of",
            "source": f"r:{rslug}",
            "target": f"a:{m['artist_slug']}",
            "tipo": "member_of",
            "relacion": ETIQUETA_TIPO["member_of"],
            "etiqueta": f"{', '.join(m['roles']) or 'miembro'} ({rango})",
            "estado": "musicbrainz",
        }})

    for i, e in enumerate(curadas):
        clave = (e["red"], e["artista"], e["tipo"])
        if clave in vistos:
            continue
        vistos.add(clave)
        if e["artista"] not in slugs_artistas:
            raise SystemExit(f"arista curada apunta a artista desconocido: {e}")
        edges.append({"data": {
            "id": f"e:{e['red']}:{e['artista']}:{e['tipo']}:{i}",
            "source": f"r:{e['red']}",
            "target": f"a:{e['artista']}",
            "tipo": e["tipo"],
            "relacion": ETIQUETA_TIPO[e["tipo"]],
            "etiqueta": e["etiqueta"],
            "estado": "prototipo",
        }})

    OUT_PATH.write_text(json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    mb = sum(1 for e in edges if e["data"]["estado"] == "musicbrainz")
    print(f"[grafo] {len(nodes)} nodos, {len(edges)} aristas ({mb} musicbrainz, {len(edges)-mb} prototipo)")


if __name__ == "__main__":
    main()
