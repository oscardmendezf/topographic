#!/usr/bin/env python3
"""Canciones destacadas por el propio atlas, extraídas de sus fichas.

Las fichas citan los títulos entre comillas latinas («…»). Este script cruza
esas citas con el tracklist verificado de cada álbum (data/canciones.json) y
marca qué pistas destaca la ficha. No inventa nada: una pista solo se marca si
su título coincide con una cita del texto de SU álbum.

El peso depende de DÓNDE se la cita, no de cuántas veces:

  3 — en la entradilla (el veredicto breve: solo nombra lo esencial)
  2 — en «Recepción y legado» (lo que quedó del disco)
  1 — solo en «La historia» / «La producción» (mención descriptiva)

Solo se marcan las pistas de peso máximo del álbum cuando ese máximo es ≥ 2.
Un álbum cuyas canciones solo aparecen descritas no recibe marca: el 71 % de
las pistas está citado en algún lado, así que marcarlas todas no distinguiría
nada. Cobertura real: ~550 pistas en ~390 álbumes.

Los movimientos de una suite cuentan para la pista que los contiene
(«Total Mass Retain» marca «Close to the Edge: …»).

Salida: data/destacadas.json

Uso:  python3 pipeline/build_destacadas.py [--informe]

ESTADO (18-sep-2026): la extracción automática NO se usa como fuente de destacadas.
Medido sobre las 1318 fichas: marcar toda cita da el 71 % de las pistas (no distingue
nada) y ponderar por sección deja fuera los discos canónicos — «Close to the Edge»,
«The Dark Side of the Moon» y «In the Court of the Crimson King» no reciben marca y
«Wolf City» sí, porque la zona donde cada redactor nombra los títulos es una convención
de escritura, no una jerarquía. data/destacadas.json queda vacío hasta tener una fuente
real; el formato de salida de este script es el que consumirá esa fuente.

El script sigue sirviendo como verificador: las citas que no casan con ninguna pista del
álbum (--informe) delatan títulos mal escritos en las historias.
"""

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALBUMES = ROOT / "content" / "albumes"
CANCIONES = ROOT / "data" / "canciones.json"
OUT = ROOT / "data" / "destacadas.json"
MARCA = "<!-- historia:editorial -->"

SEP_SUITE = re.compile(r"\s*/\s*|\s*:\s*|\s*[–—-]\s*")
MIN_MOV = 6          # un movimiento más corto que esto no se usa como ancla (ruido)
PESOS = {"entradilla": 3, "legado": 2, "historia": 1}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("’", "'").replace("‘", "'").replace("´", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s']", " ", s.lower())).strip()


def secciones(historia: str) -> dict:
    out = {}
    for parte in re.split(r"^## ", historia, flags=re.M)[1:]:
        titulo, _, cuerpo = parte.partition("\n")
        out[titulo.strip()] = cuerpo
    return out


def main() -> None:
    informe = "--informe" in sys.argv
    canciones = json.loads(CANCIONES.read_text(encoding="utf-8"))
    out, stats, sin_match = {}, Counter(), Counter()

    for md in sorted(ALBUMES.glob("*.md")):
        lista = canciones.get(md.stem)
        if not lista:
            continue
        cuerpo = md.read_text(encoding="utf-8").split("---\n", 2)[-1]
        entradilla, _, historia = cuerpo.partition(MARCA)
        sec = secciones(historia)
        zonas = {
            "entradilla": entradilla,
            "legado": sec.get("Recepción y legado", ""),
            "historia": sec.get("La historia", "") + sec.get("La producción", ""),
        }

        indice = {}
        for m in lista["medios"]:
            for p in m["pistas"]:
                indice.setdefault(norm(p["titulo"]), p["n"])
                for mov in SEP_SUITE.split(p["titulo"]):
                    if len(norm(mov)) >= MIN_MOV:
                        indice.setdefault(norm(mov), p["n"])

        mejor: dict[int, dict] = {}
        for zona, texto in zonas.items():
            for cita in re.findall(r"«([^»]{2,90})»", texto):
                n = indice.get(norm(cita))
                if n is None:
                    sin_match[cita] += 1
                    continue
                peso = PESOS[zona]
                if peso > mejor.get(n, {}).get("peso", 0):
                    mejor[n] = {"peso": peso, "donde": zona, "cita": cita}

        if not mejor:
            stats["álbumes sin ninguna cita"] += 1
            continue
        top = max(d["peso"] for d in mejor.values())
        if top < 2:
            stats["álbumes solo con menciones descriptivas (sin marca)"] += 1
            continue
        pistas = {str(n): d for n, d in sorted(mejor.items()) if d["peso"] == top}
        out[md.stem] = {
            "fuente": "editorial",
            "criterio": "citada en la entradilla o en «Recepción y legado» de su propia ficha",
            "pistas": pistas,
        }
        stats["álbumes con canciones destacadas"] += 1
        stats[f"pistas marcadas (peso {top})"] += len(pistas)

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    marcadas = sum(len(v["pistas"]) for v in out.values())
    total = sum(len(m["pistas"]) for a in canciones.values() for m in a["medios"])
    print(f"[destacadas] {marcadas} de {total} pistas marcadas en {len(out)} de {len(canciones)} álbumes"
          f" → {OUT.relative_to(ROOT)}")
    for k, v in sorted(stats.items()):
        print(f"   {k}: {v}")
    if informe:
        print("\n[destacadas] citas que no son una pista de su álbum (las 30 más frecuentes):")
        for c, n in sin_match.most_common(30):
            print(f"   {n:4d}  «{c}»")


if __name__ == "__main__":
    main()
