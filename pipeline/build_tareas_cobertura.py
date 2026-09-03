#!/usr/bin/env python3
"""Cobertura total: manifiesto de todos los álbumes de estudio del atlas
(1966-hoy) que aún no tienen ficha ni exclusión. Agrupa en tareas de
redacción balanceadas (~35 álbumes máx.; artistas grandes se parten por era).

Salida: data/tareas_cobertura.json
Uso:  python3 pipeline/build_tareas_cobertura.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_editorial import ATLAS_PATH, CONTENT, slugify
from expand_eras import era_de

ROOT = Path(__file__).resolve().parent.parent
MAX_LOTE = 35


def main() -> None:
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    excluidos = json.loads((ROOT / "data" / "albumes_excluidos.json").read_text(encoding="utf-8"))
    slugs_exc = {e["slug"] for e in excluidos}
    mbids_exc = {e.get("mbid") for e in excluidos}
    nombres = {a["slug"]: a["nombre"] for a in atlas["nodos"]["artistas"]}

    rgids_ficha = set()
    for p in (CONTENT / "albumes").glob("*.md"):
        m = re.search(r'^mb_rgid: "([a-f0-9-]+)"$', p.read_text(encoding="utf-8"), flags=re.M)
        if m:
            rgids_ficha.add(m.group(1))

    pendientes = {}
    SUF = sys.argv[1] if len(sys.argv) > 1 else ""
    for x in atlas["nodos"]["albumes"]:
        sec = set(x.get("tipos_secundarios", []))
        if x.get("tipo_primario") != "Album" or (sec and sec != {"Soundtrack"}):
            continue
        if not x["primer_lanzamiento"]:
            continue
        s = x["artist_slug"]
        slug = f"{s}-{slugify(x['titulo'])}"
        if x["mbid"] in rgids_ficha or x["mbid"] in mbids_exc or slug in slugs_exc:
            continue
        anio = int(x["primer_lanzamiento"][:4])
        pendientes.setdefault(s, []).append({
            "album_slug": slug, "titulo": x["titulo"], "anio": anio,
            "era": era_de(anio), "mbid": x["mbid"],
        })

    # particionar artistas grandes por era y empaquetar en lotes
    unidades = []
    for s, albs in sorted(pendientes.items(), key=lambda kv: -len(kv[1])):
        albs.sort(key=lambda a: a["anio"])
        if len(albs) > MAX_LOTE:
            for era in ("clasica", "siguiente", "moderna"):
                sub = [a for a in albs if a["era"] == era]
                for i in range(0, len(sub), MAX_LOTE):
                    unidades.append((f"{s}-{era}-{i // MAX_LOTE + 1}", s, sub[i:i + MAX_LOTE]))
        else:
            unidades.append((s, s, albs))

    tareas, actual, tam = [], [], 0
    for uid, s, albs in unidades:
        if tam + len(albs) > MAX_LOTE and actual:
            tareas.append(actual)
            actual, tam = [], 0
        actual.append({"unidad": uid, "artista_slug": s, "artista": nombres[s], "albumes": albs})
        tam += len(albs)
    if actual:
        tareas.append(actual)

    grupos = [{"id": f"cob{SUF}-{i+1:02d}", "unidades": t, "total": sum(len(u["albumes"]) for u in t)}
              for i, t in enumerate(tareas)]
    (ROOT / "data" / f"tareas_cobertura{SUF}.json").write_text(
        json.dumps({"grupos": grupos}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    total = sum(g["total"] for g in grupos)
    print(f"[cobertura] {total} álbumes pendientes en {len(grupos)} lotes:")
    for g in grupos:
        arts = ", ".join(sorted({u['artista_slug'] for u in g['unidades']}))
        print(f"  {g['id']}: {g['total']:3d} álbumes — {arts}")


if __name__ == "__main__":
    main()
