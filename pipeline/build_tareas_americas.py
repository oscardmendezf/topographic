#!/usr/bin/env python3
"""Fase Américas: arma data/tareas_americas.json (mismo formato que tareas_f3,
pero sin texto_fuente — no hay prototipo: la curaduría es de los redactores,
con selección esencial acotada por las reglas del workflow).

Uso:  python3 pipeline/build_tareas_americas.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_editorial import ATLAS_PATH, slugify

DATA = Path(__file__).resolve().parent.parent / "data"

GRUPOS = [
    {"id": "eeuu-1", "escena": "eeuu", "artistas": ["kansas", "styx"]},
    {"id": "eeuu-2", "escena": "eeuu", "artistas": ["utopia", "happy-the-man", "dixie-dregs"]},
    {"id": "zappa", "escena": "eeuu", "artistas": ["frank-zappa", "mothers-of-invention"]},
    {"id": "argentina", "escena": "latinoamerica", "artistas": ["crucis", "invisible", "la-maquina-de-hacer-pajaros", "mia", "espiritu"]},
    {"id": "chile-brasil", "escena": "latinoamerica", "artistas": ["los-jaivas", "congreso", "os-mutantes", "o-terco"]},
]


def main() -> None:
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    rgs = {}
    for alb in atlas["nodos"]["albumes"]:
        if alb["es_estudio"]:
            rgs.setdefault(alb["artist_slug"], []).append(alb)

    tareas = []
    for g in GRUPOS:
        artistas = []
        for slug in g["artistas"]:
            catalogo = [{
                "album_slug": f"{slug}-{slugify(a['titulo'])}",
                "titulo": a["titulo"],
                "anio": int(a["primer_lanzamiento"][:4]) if a["primer_lanzamiento"] else None,
                "mbid": a["mbid"],
            } for a in sorted(rgs.get(slug, []), key=lambda x: x["primer_lanzamiento"] or "9999")]
            if not catalogo:
                print(f"[americas] AVISO: {slug} sin álbumes de estudio en el atlas")
            artistas.append({"slug": slug, "catalogo": catalogo})
        tareas.append({
            "id": g["id"], "escena": g["escena"], "texto_fuente": None, "artistas": artistas,
        })

    (DATA / "tareas_americas.json").write_text(
        json.dumps({"grupos": tareas}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n = sum(len(a["catalogo"]) for t in tareas for a in t["artistas"])
    print(f"[americas] {len(tareas)} grupos, {n} álbumes de estudio candidatos")


if __name__ == "__main__":
    main()
