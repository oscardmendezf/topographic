#!/usr/bin/env python3
"""Genera el manifiesto data/tareas_historias.json: lotes de ~20 álbumes con las
anclas verificadas que cada agente redactor debe usar (tracklist de la edición
original, créditos de MusicBrainz, fecha de primer lanzamiento, análisis actual).

Uso:  python3 pipeline/build_tareas_historias.py [tamaño_lote]
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "albumes"
OUT = ROOT / "data" / "tareas_historias.json"
LOTE = int(sys.argv[1]) if len(sys.argv) > 1 else 20

# Créditos útiles para la producción original (no los de reedición/fabricación).
TIPOS_PROD = {"producer", "engineer", "mix", "recording", "arranger", "orchestrator",
              "conductor", "instrument arranger", "vocal arranger", "chorus master",
              "performing orchestra", "programming", "composer", "lyricist"}
TIPOS_ARTE = {"design", "design/illustration", "graphic design", "art direction",
              "illustration", "artwork", "photography"}
TIPOS_LUGAR = {"recorded at", "mixed at", "engineered at"}


def parse_md(path: Path) -> tuple[dict, str]:
    txt = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.S)
    fm, body = {}, txt
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip()
                if v.startswith('"') and v.endswith('"'):
                    v = json.loads(v)
                fm[k.strip()] = v
        body = m.group(2)
    # Si ya hay historia, el análisis es lo anterior al marcador.
    body = body.split("<!-- historia:editorial -->")[0].strip()
    return fm, body


def resumen_creditos(cred: dict) -> dict:
    out = {"produccion": [], "musicos": [], "arte": [], "lugares": []}
    vistos = set()
    for r in cred.get("rels", []):
        clave = (r["tipo"], r["nombre"], tuple(r.get("atributos", [])))
        if clave in vistos:
            continue
        vistos.add(clave)
        attrs = ", ".join(r.get("atributos", []))
        item = f"{r['nombre']} ({r['tipo']}{': ' + attrs if attrs else ''})"
        if r["target"] == "place" and r["tipo"] in TIPOS_LUGAR:
            out["lugares"].append(f"{r['nombre']} ({r['tipo']})")
        elif r["tipo"] in TIPOS_PROD:
            out["produccion"].append(item)
        elif r["tipo"] in ("instrument", "vocal", "performer"):
            out["musicos"].append(f"{r['nombre']}: {attrs or r['tipo']}")
        elif r["tipo"] in TIPOS_ARTE:
            out["arte"].append(item)
    for k in out:
        out[k] = out[k][:40]
    return out


def main() -> None:
    canciones = json.loads((ROOT / "data" / "canciones.json").read_text(encoding="utf-8"))
    creditos = json.loads((ROOT / "data" / "creditos.json").read_text(encoding="utf-8"))
    artistas = {}
    for p in (ROOT / "content" / "artistas").glob("*.md"):
        fm, body = parse_md(p)
        artistas[fm.get("slug", p.stem)] = body[:900]

    albumes = []
    for p in sorted(CONTENT.glob("*.md")):
        fm, analisis = parse_md(p)
        slug = fm["slug"]
        lista = canciones.get(slug)
        pistas = []
        if lista:
            for i, m in enumerate(lista["medios"]):
                pref = f"[{m.get('formato') or 'Disco'} {i + 1}] " if len(lista["medios"]) > 1 else ""
                for t in m["pistas"]:
                    dur = f" ({t['ms'] // 60000}:{(t['ms'] // 1000) % 60:02d})" if t.get("ms") else ""
                    pistas.append(f"{pref}{t['n']}. {t['titulo']}{dur}")
        albumes.append({
            "album_slug": slug, "titulo": fm["titulo"], "artista": fm["artista"],
            "artista_slug": fm["artista_slug"], "anio": int(fm["anio_ficha"]),
            "primer_lanzamiento": fm.get("primer_lanzamiento"), "era": fm.get("era"),
            "analisis_actual": analisis, "pistas": pistas,
            "creditos_mb": resumen_creditos(creditos.get(slug, {})),
        })

    # Lotes contiguos por artista (orden alfabético de slug = agrupa por artista).
    albumes.sort(key=lambda a: (a["artista_slug"], a["anio"], a["album_slug"]))
    grupos, actual = [], []
    for a in albumes:
        if len(actual) >= LOTE and a["artista_slug"] != actual[-1]["artista_slug"]:
            grupos.append(actual)
            actual = []
        elif len(actual) >= LOTE + 6:  # artista muy largo: cortar igual
            grupos.append(actual)
            actual = []
        actual.append(a)
    if actual:
        grupos.append(actual)

    manifest = {"grupos": []}
    for i, g in enumerate(grupos, 1):
        slugs_art = sorted({a["artista_slug"] for a in g})
        manifest["grupos"].append({
            "id": f"his-{i:02d}",
            "contexto_artistas": {s: artistas.get(s, "") for s in slugs_art},
            "albumes": g,
        })
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # Un archivo por grupo para que cada agente lea solo lo suyo.
    por_grupo = ROOT / "data" / "tareas_historias"
    por_grupo.mkdir(exist_ok=True)
    for g in manifest["grupos"]:
        (por_grupo / f"{g['id']}.json").write_text(json.dumps(g, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[historias] {len(albumes)} álbumes en {len(grupos)} grupos → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
