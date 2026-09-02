#!/usr/bin/env python3
"""Aplica los resultados de los redactores F3 (data/editorial_f3/*.json):

- content/artistas/<slug>.md para los 23 artistas de escena (frontmatter del
  atlas + escena; cuerpo = ficha editorial del agente, derivada de Fronteras).
- content/albumes/<slug>.md SOLO para los álbumes nombrados en el prototipo
  (regla F3: discografías clásicas nombradas título por título).
  Charts del texto del prototipo -> estado 'memoria' + estrellas por fórmula;
  sin charts -> 's.d.' + estrellas comerciales editoriales.

Lint: ningún texto nuevo con posiciones de chart.
Uso:  python3 pipeline/merge_f3.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_editorial import ATLAS_PATH, CONTENT, write_md
from expand_eras import era_de, estrellas_de_charts
from merge_editorial_f2 import RE_CHART

ROOT = Path(__file__).resolve().parent.parent
SEED = json.loads((ROOT / "pipeline" / "artists_seed.json").read_text(encoding="utf-8"))["artistas"]

# uso: merge_f3.py [nombre]  -> lee data/editorial_<nombre>/ y data/tareas_<nombre>.json
NOMBRE = sys.argv[1] if len(sys.argv) > 1 else "f3"
F3 = ROOT / "data" / f"editorial_{NOMBRE}"


def main() -> None:
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    art_atlas = {a["slug"]: a for a in atlas["nodos"]["artistas"]}
    alb_por_mbid = {a["mbid"]: a for a in atlas["nodos"]["albumes"]}
    seed = {s["slug"]: s for s in SEED}
    manifest = json.loads((ROOT / "data" / f"tareas_{NOMBRE}.json").read_text(encoding="utf-8"))
    info_alb = {}
    for g in manifest["grupos"]:
        for art in g["artistas"]:
            for c in art["catalogo"]:
                info_alb[c["album_slug"]] = {**c, "artista_slug": art["slug"]}

    lint, n_art, n_alb = [], 0, 0
    for jpath in sorted(F3.glob("*.json")):
        data = json.loads(jpath.read_text(encoding="utf-8"))
        for art in data["artistas"]:
            slug = art["slug"]
            a = art_atlas.get(slug)
            if not a:
                print(f"[f3] AVISO: {slug} no está en el atlas, salto")
                continue
            if RE_CHART.search(art.get("ficha") or ""):
                lint.append(f"artista {slug}")
            write_md(CONTENT / "artistas" / f"{slug}.md", {
                "tipo": "artista", "slug": slug, "nombre": a["nombre"],
                "escena": seed.get(slug, {}).get("escena"),
                "fase": seed.get(slug, {}).get("fase"),
                "mbid": a["mbid"], "discogs_id": a["discogs_id"],
                "wikipedia_url": a["wikipedia_url"],
            }, (art.get("ficha") or "").strip())
            n_art += 1

            for alb in art.get("albumes", []):
                aslug = alb["album_slug"]
                info = info_alb.get(aslug)
                if not info:
                    print(f"[f3] AVISO: álbum fuera de manifiesto: {aslug}")
                    continue
                if RE_CHART.search(alb.get("analisis") or ""):
                    lint.append(f"álbum {aslug}")
                rg = alb_por_mbid.get(info["mbid"], {})
                anio = info["anio"] or 0
                charts = (alb.get("charts_texto") or "").strip() or "s.d."
                est_charts = estrellas_de_charts(charts)
                meta = {
                    "tipo": "album", "slug": aslug, "titulo": info["titulo"],
                    "artista": a["nombre"], "artista_slug": slug,
                    "anio_ficha": anio, "era": era_de(anio),
                    "escena": seed.get(slug, {}).get("escena"),
                    "mb_rgid": info["mbid"],
                    "primer_lanzamiento": rg.get("primer_lanzamiento"),
                    "charts_texto": charts,
                    "charts_estado": "memoria" if charts != "s.d." else "sd",
                    "estrellas_critica": alb.get("estrellas_critica"),
                    "critica_fuente": "editorial",
                    "critica_nota": alb.get("critica_nota"),
                }
                if est_charts is not None:
                    meta["estrellas_comercial"] = est_charts
                    meta["comercial_fuente"] = "charts"
                else:
                    meta["estrellas_comercial"] = alb.get("estrellas_comercial")
                    meta["comercial_fuente"] = "editorial"
                    if alb.get("comercial_nota"):
                        meta["comercial_nota"] = alb["comercial_nota"]
                write_md(CONTENT / "albumes" / f"{aslug}.md", meta, (alb.get("analisis") or "").strip())
                n_alb += 1

    print(f"[f3] artistas escritos: {n_art} · álbumes escritos: {n_alb}")
    if lint:
        print(f"[f3] LINT — textos con datos de chart ({len(lint)}): {lint}")
        sys.exit(1)


if __name__ == "__main__":
    main()
