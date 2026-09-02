#!/usr/bin/env python3
"""Atlas del Prog — Fase 2: eras siguiente (1981-1999) y moderna (2000-hoy).

1. Parsea la continuación del prototipo (bloques 81-83 … 14-hoy): fichas
   individuales (texto editorial + charts, estado 'memoria' según el propio
   encabezado del prototipo) y bloques de etapa -> content/etapas/.
2. Crea una ficha markdown por cada álbum de estudio 1981+ de los 25 artistas
   prog (los conceptuales no-prog quedan congelados en la era clásica, como
   en el prototipo). Cuerpo vacío si no hay texto del prototipo.
3. Agrega a TODAS las fichas de álbum: `era` y, donde hay charts parseables,
   `estrellas_comercial` con fuente 'charts'. Fórmula (mejor pico UK/US):
   1-2 -> 5★ · 3-10 -> 4★ · 11-30 -> 3★ · 31-75 -> 2★ · 76+ o «—» -> 1★.
   Sin dato -> queda para la capa editorial (agentes).
4. Emite data/tareas_editorial.json: qué le falta a cada álbum (análisis,
   estrellas de crítica, comercial editorial) para el fan-out de agentes.

Uso:  python3 pipeline/expand_eras.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_editorial import (
    HTML_PATH, ATLAS_PATH, CONTENT, RE_YEAR, clean, slugify, norm_title,
    frontmatter, write_md, MANUAL_MATCHES,
)

TAREAS_PATH = Path(__file__).resolve().parent.parent / "data" / "tareas_editorial.json"
NPR = {"beatles", "pretty-things", "kinks", "small-faces"}

RE_ART_CONT = re.compile(
    r'<article class="al" data-b="(?P<b>\w+)"><span class="bar"></span>'
    r'<div><h4>(?P<titulo>.*?) <em>(?P<em>.*?)</em></h4>'
    r'<p>(?P<analisis>.*?)</p></div><span class="c">(?P<charts>.*?)</span></article>'
)


def era_de(anio: int) -> str:
    if anio <= 1980:
        return "clasica"
    if anio <= 1999:
        return "siguiente"
    return "moderna"


def estrellas_de_charts(charts: str) -> int | None:
    """Mejor pico entre los números UK/US del texto de charts."""
    picos = [int(x) for x in re.findall(r"(?:UK|US)\s+(\d+)", charts)]
    if picos:
        p = min(picos)
        return 5 if p <= 2 else 4 if p <= 10 else 3 if p <= 30 else 2 if p <= 75 else 1
    if "—" in charts:  # no entró en listas
        return 1
    return None  # s.d.


def parsear_continuacion(src: str):
    sec = src.split('<main id="tiempo">')[1].split("</main>")[0]
    fichas, etapas = [], []
    en_cont = False
    for line in sec.splitlines():
        ym = RE_YEAR.search(line)
        if ym:
            en_cont = not re.fullmatch(r"\d{4}", ym.group("y"))
            continue
        if not en_cont or "<article" not in line:
            continue
        m = RE_ART_CONT.search(line)
        if not m:
            raise SystemExit(f"continuación no parseada: {line.strip()[:120]}")
        titulo = clean(m.group("titulo"))
        em = clean(m.group("em"))
        analisis = clean(m.group("analisis"))
        charts = clean(m.group("charts"))
        anio_m = re.search(r" · (\d{4})$", em)
        if titulo.startswith("Etapa"):
            etapas.append({"b": m.group("b"), "titulo": titulo, "analisis": analisis})
        elif anio_m:
            fichas.append({
                "b": m.group("b"), "titulo": titulo, "anio": int(anio_m.group(1)),
                "analisis": analisis, "charts": charts,
            })
        else:
            raise SystemExit(f"ficha de continuación sin año ni 'Etapa': {titulo}")
    return fichas, etapas


def agregar_campos(path: Path, campos: dict) -> None:
    """Inserta campos en el frontmatter de un md existente (si no están ya)."""
    texto = path.read_text(encoding="utf-8")
    cuerpo = texto.split("---\n", 2)
    fm = cuerpo[1]
    nuevos = [f"{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, str) else ('null' if v is None else v)}"
              for k, v in campos.items() if f"{k}:" not in fm]
    if nuevos:
        cuerpo[1] = fm + "\n".join(nuevos) + "\n"
        path.write_text("---\n".join(cuerpo), encoding="utf-8")


def main() -> None:
    src = HTML_PATH.read_text(encoding="utf-8")
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    fichas_cont, etapas = parsear_continuacion(src)
    print(f"[eras] continuación del prototipo: {len(fichas_cont)} fichas, {len(etapas)} bloques de etapa")

    # --- bloques de etapa -> content/etapas/ -----------------------------
    for e in etapas:
        slug = f"{e['b']}-{slugify(e['titulo'])}"
        write_md(CONTENT / "etapas" / f"{slug}.md", {
            "tipo": "etapa", "slug": slug, "artista_slug": e["b"], "titulo": e["titulo"],
        }, e["analisis"])

    # --- índice de RGs y matching de fichas de continuación --------------
    rgs = {}
    for alb in atlas["nodos"]["albumes"]:
        if alb["es_estudio"]:
            rgs.setdefault(alb["artist_slug"], []).append(alb)

    def match_rg(aslug: str, titulo: str):
        manual = MANUAL_MATCHES.get((aslug, titulo))
        objetivo = norm_title(titulo)
        for c in rgs.get(aslug, []):
            if manual and c["mbid"] == manual:
                return c
            if norm_title(c["titulo"] or "") == objetivo:
                return c
        return None

    hechos = set()      # mbids de RG ya cubiertos por ficha del prototipo
    sin_match = []
    for f in fichas_cont:
        rg = match_rg(f["b"], f["titulo"])
        if rg:
            hechos.add(rg["mbid"])
        else:
            sin_match.append(f"{f['b']}: {f['titulo']} ({f['anio']})")
        slug = f"{f['b']}-{slugify(f['titulo'])}"
        estrellas = estrellas_de_charts(f["charts"])
        meta = {
            "tipo": "album", "slug": slug, "titulo": f["titulo"],
            "artista": None, "artista_slug": f["b"], "anio_ficha": f["anio"],
            "era": era_de(f["anio"]),
            "mb_rgid": rg["mbid"] if rg else None,
            "primer_lanzamiento": rg["primer_lanzamiento"] if rg else None,
            "charts_texto": f["charts"], "charts_estado": "memoria",
        }
        if estrellas is not None:
            meta["estrellas_comercial"] = estrellas
            meta["comercial_fuente"] = "charts"
        write_md(CONTENT / "albumes" / f"{slug}.md", meta, f["analisis"])

    # --- fichas nuevas para el resto del catálogo 1981+ -------------------
    nuevas = 0
    for aslug, albs in rgs.items():
        if aslug in NPR:
            continue
        for alb in albs:
            fecha = alb["primer_lanzamiento"] or ""
            if not fecha or fecha[:4] < "1981" or alb["mbid"] in hechos:
                continue
            anio = int(fecha[:4])
            slug = f"{aslug}-{slugify(alb['titulo'])}"
            path = CONTENT / "albumes" / f"{slug}.md"
            if path.exists():
                continue
            write_md(path, {
                "tipo": "album", "slug": slug, "titulo": alb["titulo"],
                "artista": None, "artista_slug": aslug, "anio_ficha": anio,
                "era": era_de(anio), "mb_rgid": alb["mbid"],
                "primer_lanzamiento": alb["primer_lanzamiento"],
                "charts_texto": "s.d.", "charts_estado": "sd",
            }, "")
            nuevas += 1

    # --- era + estrellas_comercial en todas las fichas --------------------
    nombres = {a["slug"]: a["nombre"] for a in atlas["nodos"]["artistas"]}
    tareas = {}
    for path in sorted((CONTENT / "albumes").glob("*.md")):
        texto = path.read_text(encoding="utf-8")
        fm = texto.split("---\n", 2)[1]
        get = lambda k: (re.search(rf'^{k}: (.*)$', fm, flags=re.M) or [None, None])[1]
        aslug = json.loads(get("artista_slug"))
        anio = int(get("anio_ficha"))
        charts = json.loads(get("charts_texto"))
        campos = {"era": era_de(anio)}
        if get("artista") == "null":
            campos_artista = {"artista": nombres.get(aslug, aslug)}
            # 'artista' ya existe como clave null -> reemplazo directo
            texto = texto.replace("artista: null\n", f'artista: {json.dumps(nombres.get(aslug, aslug), ensure_ascii=False)}\n', 1)
            path.write_text(texto, encoding="utf-8")
        estrellas = estrellas_de_charts(charts)
        if estrellas is not None:
            campos["estrellas_comercial"] = estrellas
            campos["comercial_fuente"] = "charts"
        agregar_campos(path, campos)

        # manifiesto de tareas para los agentes
        texto = path.read_text(encoding="utf-8")
        fm2, cuerpo = texto.split("---\n", 2)[1:3]
        grupo = "npr" if aslug in NPR else aslug
        tareas.setdefault(grupo, []).append({
            "slug": path.stem,
            "titulo": json.loads((re.search(r'^titulo: (.*)$', fm2, flags=re.M)).group(1)),
            "anio": anio,
            "era": era_de(anio),
            "tiene_analisis": bool(cuerpo.strip()),
            "necesita_comercial": "estrellas_comercial" not in fm2,
            "mb_rgid": None if "mb_rgid: null" in fm2 else "ok",
        })

    TAREAS_PATH.write_text(json.dumps({
        "instrucciones": "ver prompt del workflow",
        "artistas": tareas,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    total = sum(len(v) for v in tareas.values())
    sin_analisis = sum(1 for v in tareas.values() for t in v if not t["tiene_analisis"])
    sin_com = sum(1 for v in tareas.values() for t in v if t["necesita_comercial"])
    print(f"[eras] fichas nuevas sin texto: {nuevas} · total fichas: {total}")
    print(f"[eras] pendientes de análisis: {sin_analisis} · pendientes de comercial editorial: {sin_com}")
    if sin_match:
        print(f"[eras] fichas de continuación SIN match en atlas ({len(sin_match)}):")
        for s in sin_match:
            print("   ", s)


if __name__ == "__main__":
    main()
