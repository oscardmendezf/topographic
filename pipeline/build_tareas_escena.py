#!/usr/bin/env python3
"""Manifiesto editorial para una ampliación de escena (mismo formato que
tareas_americas.json, consumido por merge_f3.py <nombre>), con anclas
verificadas de MusicBrainz para los redactores: catálogo completo de estudio,
formaciones (member_of con fechas y roles), país, años de actividad y enlaces.

Regla de cobertura total: cada álbum del catálogo debe salir con ficha o con
exclusión motivada (merge_f3.py registra `excluidos` en albumes_excluidos.json).

Uso:  python3 pipeline/build_tareas_escena.py <nombre>
      (los grupos de <nombre> se definen en CONFIG)
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_editorial import ATLAS_PATH, slugify

DATA = Path(__file__).resolve().parent.parent / "data"

CONFIG = {
    "argentina2": {
        "escena": "latinoamerica",
        "grupos": [
            {"id": "ar-spinetta", "artistas": ["almendra", "pescado-rabioso", "spinetta-jade", "socios-del-desierto"]},
            {"id": "ar-spinetta-solo", "artistas": ["spinetta"]},
            {"id": "ar-garcia", "artistas": ["sui-generis", "porsuigieco", "seru-giran"]},
            {"id": "ar-garcia-solo", "artistas": ["charly-garcia"]},
            {"id": "ar-sinfonico", "artistas": ["aquelarre", "arco-iris", "alas", "color-humano"]},
            {"id": "ar-otros", "artistas": ["vox-dei", "pastoral", "bubu", "tantor"]},
        ],
    },
}


def main() -> None:
    nombre = sys.argv[1] if len(sys.argv) > 1 else "argentina2"
    conf = CONFIG[nombre]
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    art_atlas = {a["slug"]: a for a in atlas["nodos"]["artistas"]}
    rgs, miembros = {}, {}
    for alb in atlas["nodos"]["albumes"]:
        sec = set(alb.get("tipos_secundarios", []))
        if alb.get("tipo_primario") != "Album" or (sec and sec != {"Soundtrack"}):
            continue
        if not alb["primer_lanzamiento"]:
            continue
        rgs.setdefault(alb["artist_slug"], []).append(alb)
    for m in atlas["aristas"]["member_of"]:
        miembros.setdefault(m["artist_slug"], []).append(
            f"{m['person_nombre']} ({', '.join(m['roles']) or 'miembro'}; {m['desde'] or '?'}–{m['hasta'] or ('act.' if m['vigente'] else '?')})")

    tareas = []
    for g in conf["grupos"]:
        artistas = []
        for slug in g["artistas"]:
            a = art_atlas.get(slug)
            if not a:
                print(f"[escena] AVISO: {slug} no está en el atlas (¿falta fetch/normalize?)")
                continue
            albs = sorted(rgs.get(slug, []), key=lambda x: x["primer_lanzamiento"] or "9999")
            base = [f"{slug}-{slugify(x['titulo'])}" for x in albs]
            dup = {s for s, n in Counter(base).items() if n > 1}
            catalogo = []
            for x, s in zip(albs, base):
                anio = int(x["primer_lanzamiento"][:4])
                if s in dup:
                    s = f"{s}-{anio}"
                catalogo.append({"album_slug": s, "titulo": x["titulo"], "anio": anio, "mbid": x["mbid"],
                                 "primer_lanzamiento": x["primer_lanzamiento"],
                                 "soundtrack": "Soundtrack" in set(x.get("tipos_secundarios", []))})
            if not catalogo:
                print(f"[escena] AVISO: {slug} sin álbumes de estudio en el atlas")
            artistas.append({
                "slug": slug, "nombre": a["nombre"], "tipo": a["tipo"], "pais": a["pais"],
                "inicio": a["inicio"], "fin": a["fin"], "wikipedia_url": a["wikipedia_url"],
                "formaciones_mb": miembros.get(slug, []),
                "catalogo": catalogo,
            })
        tareas.append({"id": g["id"], "escena": conf["escena"], "texto_fuente": None, "artistas": artistas})

    out = DATA / f"tareas_{nombre}.json"
    out.write_text(json.dumps({"grupos": tareas}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    por_grupo = DATA / f"tareas_{nombre}"
    por_grupo.mkdir(exist_ok=True)
    for t in tareas:
        (por_grupo / f"{t['id']}.json").write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n = sum(len(a["catalogo"]) for t in tareas for a in t["artistas"])
    print(f"[escena] {nombre}: {len(tareas)} grupos, {sum(len(t['artistas']) for t in tareas)} artistas, {n} álbumes → {out.relative_to(DATA.parent)}")
    for t in tareas:
        print(f"  {t['id']}: " + ", ".join(f"{a['slug']}({len(a['catalogo'])})" for a in t["artistas"]))


if __name__ == "__main__":
    main()
