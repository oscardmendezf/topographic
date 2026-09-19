#!/usr/bin/env python3
"""Capa de popularidad medida: cruza los top tracks de Last.fm (data/raw_lastfm/)
con el tracklist verificado de cada álbum y marca las piezas más escuchadas.

Salvaguarda contra homónimos: Last.fm degrada el `mbid` a su propia entidad
cuando no lo conoce, así que consultar por MBID NO garantiza el artista
correcto: `mia` devuelve a la rapera y `nirvana-uk` al grupo de Seattle. Peor,
a veces mezcla dos bandas en una misma entrada (`alas` y `egg` traen sus top
tracks revueltos con los de un homónimo).

El filtro es el cruce mismo: solo se usan los tracks cuyo título casa con una
pista de un álbum de ESE artista en el atlas. Un track ajeno no tiene con qué
cruzar, así que la contaminación se descarta sola, pista por pista, incluso
dentro de una entrada mezclada. Un artista con menos de MIN_CRUCES coincidencias
queda sin dato: no hay suficiente para sostener un ranking.

No se usa un porcentaje: los artistas con catálogo corto en el atlas tienen un
techo bajo por construcción (Museo Rosenbach tiene 17 pistas y Last.fm devuelve
50 tracks, así que nunca pasaría del 34 % aunque todo sea correcto).

La escala es relativa al artista, nunca absoluta: entre Pink Floyd y Tantor hay
un factor de 2400, así que un número global solo mediría la fama del grupo.
Se marca la posición de la pista dentro de las más escuchadas de su artista.

Salida: data/popularidad.json

Uso:  python3 pipeline/build_popularidad.py [--top N] [--informe]
"""

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw_lastfm"
OUT = DATA / "popularidad.json"
MIN_CRUCES = 3        # menos coincidencias que esto no sostienen un ranking
TOP_POR_DEFECTO = 8   # cuántas de las más escuchadas de cada artista se marcan

RE_EDICION = re.compile(
    r"\s*\((?:remaster|remastered|live|mono|stereo|single|edit|version|alternate|demo)[^)]*\)"
    r"|\s*-\s*(?:remaster(?:ed)?|\d{4}\s*remaster|live|mono|stereo|single version|demo)\b.*$", re.I)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("’", "'").replace("‘", "'")
    s = RE_EDICION.sub(" ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s']", " ", s.lower())).strip()


def main() -> None:
    top_n = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else TOP_POR_DEFECTO
    informe = "--informe" in sys.argv
    canciones = json.loads((DATA / "canciones.json").read_text(encoding="utf-8"))

    # título normalizado -> [(album_slug, medio, n)] por artista
    indice: dict[str, dict[str, list]] = {}
    for md in sorted((ROOT / "content" / "albumes").glob("*.md")):
        fm = md.read_text(encoding="utf-8").split("---\n", 2)[1]
        m = re.search(r'^artista_slug:\s*"([^"]+)"', fm, re.M)
        lista = canciones.get(md.stem)
        if not m or not lista:
            continue
        d = indice.setdefault(m.group(1), {})
        for i, medio in enumerate(lista["medios"], 1):
            for p in medio["pistas"]:
                d.setdefault(norm(p["titulo"]), []).append((md.stem, i, p["n"]))

    out: dict[str, dict] = {}
    descartados, mezclados, sin_fichas, stats = [], [], [], Counter()
    capturas = set()

    for f in sorted(RAW.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        slug, tracks = d["slug"], d["tracks"]
        idx = indice.get(slug)
        if not idx:
            sin_fichas.append(slug)
            continue
        if not tracks:
            descartados.append(f"{slug}: sin tracks")
            continue
        casan = [t for t in tracks if norm(t["titulo"]) in idx]
        if len(casan) < MIN_CRUCES:
            descartados.append(f"{slug}: solo {len(casan)} de sus {len(tracks)} top tracks existe en el "
                               f"atlas (top 1 de Last.fm: «{tracks[0]['titulo']}») — no es nuestro artista")
            continue
        # Ratio bajo con el track más escuchado ajeno = Last.fm mezcla dos bandas.
        # Ratio bajo con el top 1 propio = catálogo corto en el atlas, es normal.
        if len(casan) / len(tracks) < 0.25 and norm(tracks[0]["titulo"]) not in idx:
            mezclados.append(f"{slug}: {len(casan)}/{len(tracks)} cruzan; el más escuchado "
                             f"(«{tracks[0]['titulo']}») es de otra banda — se usa solo lo que cruza")
        capturas.add(d.get("capturado"))
        # ranking por oyentes dentro del artista, solo sobre lo que cruza
        casan.sort(key=lambda t: (-(t["listeners"] or 0), -(t["playcount"] or 0)))
        for pos, t in enumerate(casan[:top_n], 1):
            for album_slug, medio, n in idx[norm(t["titulo"])]:
                pistas = out.setdefault(album_slug, {
                    "fuente": "last.fm artist.getTopTracks",
                    "capturado": d.get("capturado"),
                    "nota": "posición dentro de las más escuchadas de su artista, no del atlas",
                    "pistas": {},
                })["pistas"]
                clave = f"{medio}:{n}"
                previo = pistas.get(clave)
                if previo and previo["puesto"] <= pos:
                    continue
                pistas[clave] = {"medio": medio, "n": n, "puesto": pos,
                                 "listeners": t["listeners"], "titulo_lastfm": t["titulo"]}
                stats["pistas marcadas"] += 1
        stats["artistas usados"] += 1

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[popularidad] {stats['artistas usados']} artistas usados · "
          f"{len(out)} álbumes con marca · {sum(len(v['pistas']) for v in out.values())} pistas "
          f"→ {OUT.relative_to(ROOT)}  (captura {sorted(capturas)[0] if capturas else '—'})")
    print(f"[popularidad] artistas descartados por no ser el nuestro en Last.fm: {len(descartados)}")
    for s in descartados:
        print("   ", s)
    if mezclados:
        print(f"[popularidad] entradas de Last.fm que mezclan dos bandas ({len(mezclados)}): "
              "se usan solo los tracks que cruzan")
        for s in mezclados:
            print("   ", s)
    if sin_fichas:
        print(f"[popularidad] sin fichas de álbum en el atlas: {sin_fichas}")
    if informe:
        print("\n[popularidad] ejemplos:")
        for slug in list(out)[:5]:
            ps = out[slug]["pistas"]
            print(f"   {slug}: " + ", ".join(f"#{v['puesto']} {v['titulo_lastfm']}" for v in list(ps.values())[:3]))


if __name__ == "__main__":
    main()
