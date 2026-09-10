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
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
NOMBRE = ARGS[0] if ARGS else "f3"
CHECK = "--check" in sys.argv   # verifica sin escribir
F3 = ROOT / "data" / f"editorial_{NOMBRE}"


def main() -> None:
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    art_atlas = {a["slug"]: a for a in atlas["nodos"]["artistas"]}
    alb_por_mbid = {a["mbid"]: a for a in atlas["nodos"]["albumes"]}
    seed = {s["slug"]: s for s in SEED}
    manifest = json.loads((ROOT / "data" / f"tareas_{NOMBRE}.json").read_text(encoding="utf-8"))
    info_alb, catalogo_de = {}, {}
    for g in manifest["grupos"]:
        for art in g["artistas"]:
            catalogo_de[art["slug"]] = [c["album_slug"] for c in art["catalogo"]]
            for c in art["catalogo"]:
                info_alb[c["album_slug"]] = {**c, "artista_slug": art["slug"]}

    EXC_PATH = ROOT / "data" / "albumes_excluidos.json"
    excluidos = json.loads(EXC_PATH.read_text(encoding="utf-8"))
    ya_exc = {e["slug"] for e in excluidos}
    lint, n_art, n_alb, n_exc = [], 0, 0, 0
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
            # cobertura del catálogo: cada álbum una vez, en albumes o excluidos
            if slug in catalogo_de:
                vistos = [a["album_slug"] for a in art.get("albumes", [])] + [e["album_slug"] for e in art.get("excluidos", [])]
                falt = [c for c in catalogo_de[slug] if c not in vistos]
                dup = {v for v in vistos if vistos.count(v) > 1}
                if falt:
                    lint.append(f"{slug}: sin ficha ni exclusión: {falt}")
                if dup:
                    lint.append(f"{slug}: duplicados: {sorted(dup)}")
            if CHECK:
                n_art += 1
                for alb in art.get("albumes", []):
                    if alb["album_slug"] not in info_alb:
                        lint.append(f"álbum fuera de manifiesto: {alb['album_slug']}")
                    if RE_CHART.search(alb.get("analisis") or ""):
                        lint.append(f"álbum {alb['album_slug']}")
                    n_alb += 1
                continue
            write_md(CONTENT / "artistas" / f"{slug}.md", {
                "tipo": "artista", "slug": slug, "nombre": a["nombre"],
                "escena": seed.get(slug, {}).get("escena"),
                "fase": seed.get(slug, {}).get("fase"),
                "mbid": a["mbid"], "discogs_id": a["discogs_id"],
                "wikipedia_url": a["wikipedia_url"],
            }, (art.get("ficha") or "").strip())
            n_art += 1

            for exc in art.get("excluidos", []):
                info = info_alb.get(exc["album_slug"])
                if not info:
                    print(f"[f3] AVISO: exclusión fuera de manifiesto: {exc['album_slug']}")
                    continue
                if exc["album_slug"] not in ya_exc:
                    excluidos.append({"slug": exc["album_slug"], "mbid": info["mbid"],
                                      "motivo": exc.get("motivo"), "fuente": f"{NOMBRE}:{jpath.stem}"})
                    ya_exc.add(exc["album_slug"])
                    n_exc += 1

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

    if not CHECK:
        EXC_PATH.write_text(json.dumps(excluidos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[f3] {'verificados' if CHECK else 'escritos'} artistas: {n_art} · álbumes escritos: {n_alb} · exclusiones nuevas: {n_exc}")
    if lint:
        print(f"[f3] LINT — textos con datos de chart ({len(lint)}): {lint}")
        sys.exit(1)


if __name__ == "__main__":
    main()
