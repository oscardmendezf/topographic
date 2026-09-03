#!/usr/bin/env python3
"""Auditoría de cobertura: ¿qué álbumes de estudio del atlas (1966-hoy) no
tienen ficha ni exclusión motivada?

Niveles de cobertura por diseño:
  - núcleo (25 artistas F1/F2): discografía completa -> todo hueco es un bug.
  - npr: solo era clásica (congelados a propósito).
  - escenas (F3/Américas): selección editorial -> se reporta cobertura, no huecos.

El match es por MBID de release-group (robusto a diferencias de slug).
Uso:  python3 pipeline/audit_cobertura.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NPR = {"beatles", "pretty-things", "kinks", "small-faces"}


def main() -> None:
    atlas = json.loads((ROOT / "data" / "atlas.json").read_text(encoding="utf-8"))
    seed = {s["slug"]: s for s in json.loads((ROOT / "pipeline" / "artists_seed.json").read_text(encoding="utf-8"))["artistas"]}
    excluidos = json.loads((ROOT / "data" / "albumes_excluidos.json").read_text(encoding="utf-8"))
    slugs_exc = {e["slug"] for e in excluidos}
    mbids_exc = {e["mbid"] for e in excluidos if e.get("mbid")}

    rgids_ficha, defectos = set(), []
    for p in (ROOT / "content" / "albumes").glob("*.md"):
        texto = p.read_text(encoding="utf-8")
        fm, cuerpo = texto.split("---\n", 2)[1:3]
        m = re.search(r'^mb_rgid: "([a-f0-9-]+)"$', fm, flags=re.M)
        if m:
            rgids_ficha.add(m.group(1))
        if not cuerpo.strip():
            defectos.append(f"sin análisis: {p.stem}")
        if "estrellas_critica:" not in fm:
            defectos.append(f"sin estrellas: {p.stem}")

    from migrate_editorial import slugify  # noqa: E402 (import tardío, mismo dir)

    huecos_nucleo, resumen = [], {"nucleo": [0, 0], "npr": [0, 0], "escena": [0, 0]}
    for x in atlas["nodos"]["albumes"]:
        # elegible: Album de estudio puro, o soundtrack de estudio propio
        sec = set(x.get("tipos_secundarios", []))
        if x.get("tipo_primario") != "Album" or (sec and sec != {"Soundtrack"}):
            continue
        if not x["primer_lanzamiento"]:
            continue
        s = x["artist_slug"]
        nivel = "npr" if s in NPR else ("escena" if seed[s].get("fase") else "nucleo")
        cubierto = x["mbid"] in rgids_ficha or x["mbid"] in mbids_exc or f"{s}-{slugify(x['titulo'])}" in slugs_exc
        resumen[nivel][0] += 1
        resumen[nivel][1] += 1 if cubierto else 0
        if nivel == "nucleo" and not cubierto:
            huecos_nucleo.append(f"{s}: {x['titulo']} ({x['primer_lanzamiento'][:4]})")

    for nivel, (tot, cub) in resumen.items():
        print(f"[auditoría] {nivel:7s}: {cub}/{tot} álbumes de estudio cubiertos (ficha o exclusión)")
    print(f"[auditoría] huecos en el núcleo: {len(huecos_nucleo)}")
    for h in huecos_nucleo:
        print("   ", h)
    print(f"[auditoría] fichas defectuosas: {len(defectos)}")
    for d in defectos[:10]:
        print("   ", d)
    if huecos_nucleo or defectos:
        sys.exit(1)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
