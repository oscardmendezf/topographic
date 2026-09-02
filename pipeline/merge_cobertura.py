#!/usr/bin/env python3
"""Aplica los resultados de la cobertura total (data/editorial_cobertura/*.json):
crea la ficha md de cada álbum incluido y registra las exclusiones (con MBID)
en data/albumes_excluidos.json. Charts siempre s.d. (no hay fuente en esta
pasada); recepción comercial editorial declarada.

Uso:  python3 pipeline/merge_cobertura.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_editorial import ATLAS_PATH, CONTENT, write_md
from merge_editorial_f2 import RE_CHART

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "data" / "editorial_cobertura"
EXC_PATH = ROOT / "data" / "albumes_excluidos.json"


def main() -> None:
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    nombres = {a["slug"]: a["nombre"] for a in atlas["nodos"]["artistas"]}
    alb_atlas = {a["mbid"]: a for a in atlas["nodos"]["albumes"]}
    manifest = json.loads((ROOT / "data" / "tareas_cobertura.json").read_text(encoding="utf-8"))
    info = {}
    for g in manifest["grupos"]:
        for u in g["unidades"]:
            for a in u["albumes"]:
                info[a["album_slug"]] = {**a, "artista_slug": u["artista_slug"]}

    excluidos = json.loads(EXC_PATH.read_text(encoding="utf-8"))
    ya = {e["slug"] for e in excluidos}
    lint, n_md, n_exc, sin_info = [], 0, 0, []

    for jpath in sorted(DIR.glob("*.json")):
        data = json.loads(jpath.read_text(encoding="utf-8"))
        for a in data["albumes"]:
            slug = a["album_slug"]
            meta_m = info.get(slug)
            if not meta_m:
                sin_info.append(f"{jpath.stem}: {slug}")
                continue
            if a.get("excluir"):
                if slug not in ya:
                    excluidos.append({"slug": slug, "mbid": meta_m["mbid"],
                                      "motivo": a.get("motivo"), "fuente": f"cobertura:{jpath.stem}"})
                    ya.add(slug)
                    n_exc += 1
                continue
            analisis = (a.get("analisis") or "").strip()
            if RE_CHART.search(analisis):
                lint.append(slug)
            rg = alb_atlas.get(meta_m["mbid"], {})
            write_md(CONTENT / "albumes" / f"{slug}.md", {
                "tipo": "album", "slug": slug, "titulo": meta_m["titulo"],
                "artista": nombres.get(meta_m["artista_slug"]),
                "artista_slug": meta_m["artista_slug"],
                "anio_ficha": meta_m["anio"], "era": meta_m["era"],
                "mb_rgid": meta_m["mbid"],
                "primer_lanzamiento": rg.get("primer_lanzamiento"),
                "charts_texto": "s.d.", "charts_estado": "sd",
                "estrellas_critica": a.get("estrellas_critica"),
                "critica_fuente": "editorial",
                "critica_nota": a.get("critica_nota"),
                "estrellas_comercial": a.get("estrellas_comercial"),
                "comercial_fuente": "editorial",
                "comercial_nota": a.get("comercial_nota"),
            }, analisis)
            n_md += 1

    EXC_PATH.write_text(json.dumps(excluidos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[cobertura] fichas creadas: {n_md} · exclusiones nuevas: {n_exc} · sin manifiesto: {len(sin_info)}")
    for s in sin_info:
        print("   ", s)
    if lint:
        print(f"[cobertura] LINT charts en análisis: {lint}")
        sys.exit(1)


if __name__ == "__main__":
    main()
