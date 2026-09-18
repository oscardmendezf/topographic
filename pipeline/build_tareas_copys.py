#!/usr/bin/env python3
"""Manifiesto editorial para las fichas largas de artista («el copy»).

Las fichas de artista del núcleo y de las escenas F3/Américas son entradillas de
2–4 líneas heredadas del prototipo; solo los 17 artistas argentinos (F7) tienen
ficha larga. Este script arma los lotes para redactar la ficha larga del resto,
con anclas verificadas: entradilla actual, formaciones de MusicBrainz, catálogo
con año y estrellas, conexiones de la red y vecinos de escena.

Uso:  python3 pipeline/build_tareas_copys.py [--todos] [--lote N] [--escena X]
      --todos  incluye también los que ya tienen copy (por defecto, solo faltantes)
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_editorial import ATLAS_PATH

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ARTISTAS = ROOT / "content" / "artistas"
ALBUMES = ROOT / "content" / "albumes"
MARCA = "<!-- copy:editorial -->"
SEED = json.loads((ROOT / "pipeline" / "artists_seed.json").read_text(encoding="utf-8"))["artistas"]

ORDEN_ESCENA = ["nucleo", "canterbury", "italia", "alemania", "eeuu", "latinoamerica", "rarezas"]


def partes(path: Path) -> tuple[str, str]:
    txt = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?\n)---\n(.*)$", txt, re.S)
    return (m.group(1), m.group(2).strip()) if m else ("", txt.strip())


def campo(fm: str, k: str) -> str | None:
    m = re.search(rf'^{k}:\s*"?([^"\n]*)"?\s*$', fm, re.M)
    v = m.group(1).strip() if m else None
    return v if v and v != "null" else None


def main() -> None:
    todos = "--todos" in sys.argv
    lote = 5
    if "--lote" in sys.argv:
        lote = int(sys.argv[sys.argv.index("--lote") + 1])
    solo_escena = sys.argv[sys.argv.index("--escena") + 1] if "--escena" in sys.argv else None

    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    art_atlas = {a["slug"]: a for a in atlas["nodos"]["artistas"]}
    seed = {s["slug"]: s for s in SEED}
    grafo = json.loads((DATA / "grafo.json").read_text(encoding="utf-8"))

    miembros: dict[str, list[str]] = {}
    for m in atlas["aristas"]["member_of"]:
        miembros.setdefault(m["artist_slug"], []).append(
            f"{m['person_nombre']} ({', '.join(m['roles']) or 'miembro'}; "
            f"{m['desde'] or '?'}–{m['hasta'] or ('act.' if m['vigente'] else '?')})")

    # Catálogo con ficha publicada, por artista.
    discos: dict[str, list[dict]] = {}
    for md in sorted(ALBUMES.glob("*.md")):
        fm, cuerpo = partes(md)
        slug = campo(fm, "artista_slug")
        if not slug:
            continue
        entradilla = cuerpo.split("<!-- historia:editorial -->")[0].strip()
        discos.setdefault(slug, []).append({
            "titulo": campo(fm, "titulo"),
            "anio": int(campo(fm, "anio_ficha") or 0),
            "estrellas_critica": campo(fm, "estrellas_critica"),
            "entradilla": entradilla,
        })

    conexiones: dict[str, list[str]] = {}
    nodos = {n["data"]["id"]: n["data"] for n in grafo["nodes"]}
    for e in grafo["edges"]:
        d = e["data"]
        if str(d.get("target", "")).startswith("a:"):
            slug = d["target"][2:]
            n = nodos.get(d["source"], {})
            conexiones.setdefault(slug, []).append(f"{n.get('label')} — {d.get('relacion')}: {d.get('etiqueta')}")

    por_escena: dict[str, list[str]] = {}
    for slug in sorted(art_atlas):
        esc = seed.get(slug, {}).get("escena") or "nucleo"
        por_escena.setdefault(esc, []).append(slug)

    fichas = []
    for esc in ORDEN_ESCENA + [e for e in por_escena if e not in ORDEN_ESCENA]:
        if solo_escena and esc != solo_escena:
            continue
        for slug in por_escena.get(esc, []):
            md = ARTISTAS / f"{slug}.md"
            if not md.exists():
                print(f"[copys] AVISO: {slug} sin ficha en content/artistas")
                continue
            fm, cuerpo = partes(md)
            tiene_copy = MARCA in cuerpo or len(cuerpo.split()) >= 150
            if tiene_copy and not todos:
                continue
            a = art_atlas[slug]
            cat = sorted(discos.get(slug, []), key=lambda x: x["anio"])
            fichas.append({
                "slug": slug, "nombre": a["nombre"], "escena": esc,
                "tipo": a["tipo"], "pais": a["pais"], "inicio": a["inicio"], "fin": a["fin"],
                "mbid": a["mbid"], "wikipedia_url": a["wikipedia_url"],
                "entradilla_actual": cuerpo.split(MARCA)[0].strip(),
                "formaciones_mb": miembros.get(slug, []),
                "conexiones_red": conexiones.get(slug, []),
                "discografia": cat,
                "vecinos_escena": [art_atlas[s]["nombre"] for s in por_escena.get(esc, []) if s != slug],
            })

    grupos, i = [], 0
    for esc in ORDEN_ESCENA + [e for e in por_escena if e not in ORDEN_ESCENA]:
        del_esc = [f for f in fichas if f["escena"] == esc]
        for j in range(0, len(del_esc), lote):
            i += 1
            grupos.append({"id": f"copy-{i:02d}-{esc}", "escena": esc, "artistas": del_esc[j:j + lote]})

    out_dir = DATA / "tareas_copys"
    out_dir.mkdir(exist_ok=True)
    (DATA / "tareas_copys.json").write_text(
        json.dumps({"grupos": [{"id": g["id"], "escena": g["escena"],
                                "artistas": [a["slug"] for a in g["artistas"]]} for g in grupos]},
                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for g in grupos:
        (out_dir / f"{g['id']}.json").write_text(json.dumps(g, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[copys] {len(fichas)} artistas sin ficha larga → {len(grupos)} grupos en data/tareas_copys/")
    for g in grupos:
        print(f"  {g['id']}: " + ", ".join(f"{a['slug']}({len(a['discografia'])})" for a in g["artistas"]))


if __name__ == "__main__":
    main()
