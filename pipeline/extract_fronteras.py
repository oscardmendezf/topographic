#!/usr/bin/env python3
"""F3: extrae las fichas de la sección «Fronteras» del prototipo y arma el
manifiesto de tareas para los agentes redactores.

- data/fronteras.json: texto editorial de cada ficha de Fronteras.
- data/tareas_f3.json: por grupo de redacción, los artistas (con su texto
  fuente) y el catálogo de estudio completo de cada uno según el atlas
  (slug candidato, título, año) para que el agente seleccione los álbumes
  nombrados en el prototipo y escriba sus fichas.

Requiere el atlas ya normalizado con los artistas F3.
Uso:  python3 pipeline/extract_fronteras.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_editorial import HTML_PATH, ATLAS_PATH, RE_NODE, clean, slugify

DATA = Path(__file__).resolve().parent.parent / "data"

# ficha de Fronteras (por su <h3>) -> slugs de artistas del seed que cubre
GRUPOS = {
    "Robert Wyatt": {"id": "wyatt", "artistas": ["robert-wyatt", "matching-mole"]},
    "Hatfield and the North": {"id": "hatfield", "artistas": ["hatfield"]},
    "National Health": {"id": "national-health", "artistas": ["national-health"]},
    "Gong": {"id": "gong", "artistas": ["gong"]},
    "Egg · Steve Hillage · Kevin Ayers": {"id": "egg-hillage-ayers", "artistas": ["egg", "steve-hillage", "kevin-ayers"]},
    "Premiata Forneria Marconi (PFM)": {"id": "pfm", "artistas": ["pfm"]},
    "Banco del Mutuo Soccorso": {"id": "banco", "artistas": ["banco"]},
    "Le Orme · Area · los demás": {"id": "italia-resto", "artistas": ["le-orme", "area", "museo-rosenbach", "il-balletto-di-bronzo", "osanna", "new-trolls"]},
    "Can": {"id": "can", "artistas": ["can"]},
    "Tangerine Dream · Klaus Schulze": {"id": "td-schulze", "artistas": ["tangerine-dream", "klaus-schulze"]},
    "Faust · Neu! · Amon Düül II · Kraftwerk": {"id": "kraut-resto", "artistas": ["faust", "neu", "amon-duul-ii", "kraftwerk"]},
    # "Weather Report · Mahavishnu Orchestra · Return to Forever": fusion, NO prog
    # según el propio prototipo — queda fuera del universo a propósito.
}


def main() -> None:
    src = HTML_PATH.read_text(encoding="utf-8")
    sec = src.split("<h2>Fronteras</h2>")[1].split("</section>")[0]
    fichas = {}
    for m in RE_NODE.finditer(sec):
        nombre = clean(m.group("nombre"))
        fichas[nombre] = {
            "tag": clean(m.group("tag")),
            "texto": clean(m.group("analisis")),
        }
    print(f"[fronteras] fichas encontradas: {list(fichas)}")

    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    rgs = {}
    for alb in atlas["nodos"]["albumes"]:
        if alb["es_estudio"]:
            rgs.setdefault(alb["artist_slug"], []).append(alb)

    tareas = []
    for nombre, g in GRUPOS.items():
        if nombre not in fichas:
            raise SystemExit(f"ficha de Fronteras no encontrada: {nombre}")
        artistas = []
        for slug in g["artistas"]:
            catalogo = [{
                "album_slug": f"{slug}-{slugify(a['titulo'])}",
                "titulo": a["titulo"],
                "anio": int(a["primer_lanzamiento"][:4]) if a["primer_lanzamiento"] else None,
                "mbid": a["mbid"],
            } for a in sorted(rgs.get(slug, []), key=lambda x: x["primer_lanzamiento"] or "9999")]
            artistas.append({"slug": slug, "catalogo": catalogo})
            if not catalogo:
                print(f"[fronteras] AVISO: {slug} sin álbumes de estudio en el atlas")
        tareas.append({
            "id": g["id"],
            "ficha_prototipo": nombre,
            "escena": fichas[nombre]["tag"],
            "texto_fuente": fichas[nombre]["texto"],
            "artistas": artistas,
        })

    (DATA / "fronteras.json").write_text(json.dumps(fichas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (DATA / "tareas_f3.json").write_text(json.dumps({"grupos": tareas}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n_alb = sum(len(a["catalogo"]) for t in tareas for a in t["artistas"])
    print(f"[fronteras] {len(tareas)} grupos de redacción, {n_alb} álbumes de estudio candidatos en el atlas")


if __name__ == "__main__":
    main()
