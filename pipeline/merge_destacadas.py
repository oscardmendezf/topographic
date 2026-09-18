#!/usr/bin/env python3
"""Aplica las canciones destacadas elegidas por los redactores.

Entrada: data/editorial_destacadas/*.json con
  {"albumes": [{"album_slug": "...", "destacadas": [{"n": 3, "estrellas": 5, "nota": "…"}]}]}

Salida:  data/destacadas.json, consumido por la ficha de álbum del sitio.

Lint (sale ≠0 y descarta ese álbum): número de pista inexistente en el tracklist
verificado, estrellas fuera de 1–5, más de 3 destacadas, nota vacía o con datos
duros (posiciones de chart, ventas, certificaciones, fechas completas).

Uso:  python3 pipeline/merge_destacadas.py [--check]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge_editorial_f2 import RE_CHART
from merge_historias import RE_DURO

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DIR = DATA / "editorial_destacadas"
OUT = DATA / "destacadas.json"
MAX_POR_ALBUM = 3
MAX_NOTA = 220


def main() -> None:
    check = "--check" in sys.argv
    canciones = json.loads((DATA / "canciones.json").read_text(encoding="utf-8"))
    out, lint, avisos, stats_vacios, n_alb, n_pistas = {}, [], [], [], 0, 0

    for jpath in sorted(DIR.glob("*.json")) + sorted(DIR.glob("partes/*/*.json")):
        data = json.loads(jpath.read_text(encoding="utf-8"))
        for alb in (data["albumes"] if "albumes" in data else [data]):
            slug = alb["album_slug"]
            lista = canciones.get(slug)
            if not lista:
                lint.append(f"{slug}: no tiene tracklist verificado")
                continue
            # Clave real: (medio, n). Sin `medio` se asume el último que contiene ese
            # número, que es como resolvía el aplanado anterior (retrocompatibilidad).
            titulos = {(i, p["n"]): p["titulo"]
                       for i, m in enumerate(lista["medios"], 1) for p in m["pistas"]}
            por_n = {}
            for (i, n), tit in titulos.items():
                por_n[n] = i
            multi = len(lista["medios"]) > 1
            elegidas = alb.get("destacadas") or []
            malo = False
            if not elegidas and (alb.get("sin_destacadas") or "").strip():
                stats_vacios.append(f"{slug}: {alb['sin_destacadas'].strip()}")
                continue
            if not 1 <= len(elegidas) <= MAX_POR_ALBUM:
                lint.append(f"{slug}: {len(elegidas)} destacadas (debe ser 1–{MAX_POR_ALBUM})")
                malo = True
            vistos = set()
            for d in elegidas:
                n = d.get("n")
                medio = d.get("medio") or por_n.get(n)
                if (medio, n) not in titulos:
                    lint.append(f"{slug}: la pista {n} (disco {medio}) no existe en el tracklist")
                    malo = True
                    continue
                if multi and not d.get("medio"):
                    avisos.append(f"{slug}: pista {n} sin «medio» en un álbum de "
                                  f"{len(lista['medios'])} discos, se asume el {medio}")
                d["medio"] = medio
                if (medio, n) in vistos:
                    lint.append(f"{slug}: pista {n} (disco {medio}) repetida")
                    malo = True
                vistos.add((medio, n))
                e = d.get("estrellas")
                if not isinstance(e, int) or not 1 <= e <= 5:
                    lint.append(f"{slug}: pista {n} con estrellas «{e}» (debe ser entero 1–5)")
                    malo = True
                nota = (d.get("nota") or "").strip()
                if not nota:
                    lint.append(f"{slug}: pista {n} sin nota")
                    malo = True
                elif len(nota) > MAX_NOTA:
                    lint.append(f"{slug}: pista {n} con nota de {len(nota)} caracteres (máx {MAX_NOTA})")
                    malo = True
                else:
                    for rx, que in ((RE_CHART, "dato de chart"), (RE_DURO, "dato duro")):
                        m = rx.search(nota)
                        if m:
                            lint.append(f"{slug}: pista {n} con {que} «{m.group(0)}»")
                            malo = True
            if malo:
                continue
            n_alb += 1
            n_pistas += len(elegidas)
            if check:
                continue
            out[slug] = {
                "fuente": "editorial",
                "criterio": "piezas clave del disco elegidas por la redacción del Atlas",
                "pistas": {f'{d["medio"]}:{d["n"]}': {"medio": d["medio"], "n": d["n"],
                                                      "estrellas": d["estrellas"],
                                                      "nota": d["nota"].strip(),
                                                      "titulo": titulos[(d["medio"], d["n"])]}
                           for d in sorted(elegidas, key=lambda x: (x["medio"], x["n"]))},
            }

    if not check:
        previo = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
        previo.update(out)
        OUT.write_text(json.dumps(previo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        total = len(previo)
    else:
        total = n_alb
    print(f"[destacadas] {'verificados' if check else 'aplicados'}: {n_alb} álbumes · "
          f"{n_pistas} canciones destacadas · acumulado en data/destacadas.json: {total}")
    if stats_vacios:
        print(f"[destacadas] álbumes declarados sin nada que destacar: {len(stats_vacios)}")
        for s in stats_vacios[:10]:
            print("   ", s)
    if avisos:
        print(f"[destacadas] avisos de disco asumido ({len(avisos)}):")
        for s in avisos[:15]:
            print("   ", s)
    if lint:
        print(f"[destacadas] LINT ({len(lint)}):")
        for s in lint[:40]:
            print("   ", s)
        sys.exit(1)


if __name__ == "__main__":
    main()
