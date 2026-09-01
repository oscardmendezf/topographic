#!/usr/bin/env python3
"""Atlas del Prog — Fase 1, punto 2: capa editorial.

Migra los análisis del prototipo mapa-del-prog.html a un markdown por nodo:

  content/artistas/<slug>.md   fichas de artista (sección «Los artistas y sus etapas»)
  content/red/<slug>.md        nodos de la red (sección «La red»)
  content/albumes/<slug>.md    fichas de álbum de la era clásica 1966-1980

Alcance estricto Fase 1: el timeline se corta en 1980; Herederos, Fronteras y la
continuación 1981-presente NO se migran (fases 2-4).

Cada álbum se intenta casar con su release-group de data/atlas.json (MBID). El texto
editorial se migra verbatim; los datos duros (charts) se marcan con su estado de
verificación según el encabezado del propio prototipo — regla del brief: ningún dato
de memoria se presenta como verificado.

Uso:  python3 pipeline/migrate_editorial.py
"""

import html
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "mapa-del-prog.html"
ATLAS_PATH = ROOT / "data" / "atlas.json"
CONTENT = ROOT / "content"
REPORT_PATH = ROOT / "data" / "editorial_report.json"

# Estado de verificación de charts por artista, transcrito del encabezado del
# prototipo (ago 2026). "verificado" = contrastado con fuentes; "parcial" = solo
# una etapa/casi completo; "memoria" = aún sin verificar (tratar como s.d.).
CHARTS_ESTADO = {
    "kc": "verificado", "cam": "verificado", "car": "verificado", "jt": "verificado",
    "elo": "verificado", "rush": "verificado", "str": "verificado", "bjh": "verificado",
    "gg": "parcial", "mb": "parcial",
}
DEFAULT_ESTADO = "memoria"

# Los conceptuales no-prog comparten data-b="npr"; el artista sale del <em>.
NPR_EM_SLUG = {
    "the beatles": "beatles",
    "the pretty things": "pretty-things",
    "the kinks": "kinks",
    "small faces": "small-faces",
}

RE_ARTICLE = re.compile(
    r'<article class="al" data-b="(?P<b>\w+)"><span class="bar"></span>'
    r'<div><h4>(?P<titulo>.*?) <em>(?P<artista>.*?)</em>(?: · (?P<anio_real>\d{4}))?</h4>'
    r'<p>(?P<analisis>.*?)</p></div><span class="c">(?P<charts>.*?)</span></article>'
)

# Retitulados donde el título de la ficha no aparece en el título del release-group
# de MusicBrainz. Verificados contra la API el 01-sep-2026:
#  - "Moving Waves" = RG "Focus II" (contiene releases titulados "Moving Waves")
#  - "ELO 2" = RG "Electric Light Orchestra II" (alias MB: "Elo 2", "ELO II")
MANUAL_MATCHES = {
    ("foc", "Moving Waves"): "1a76a454-a72e-3397-b6fb-fc351df00472",
    ("elo", "ELO 2"): "a413adb4-919c-3a4d-b004-e8b1b39a38ad",
}
RE_BAND = re.compile(r'<div class="band" data-b="(?P<b>\w+)"><h3>(?P<nombre>.*?)</h3><p>(?P<analisis>.*?)</p></div>')
RE_NODE = re.compile(r'<div class="node"><span class="tag">(?P<tag>.*?)</span><h3>(?P<nombre>.*?)</h3><p>(?P<analisis>.*?)</p></div>')
RE_YEAR = re.compile(r'<div class="year"><span class="ylabel">(?P<y>[^<]+)</span>')


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text


def norm_title(text: str) -> str:
    """Normaliza títulos para casar contra MusicBrainz (puntuación, tildes, &)."""
    text = unicodedata.normalize("NFKD", text).replace("’", "'")
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = text.replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "", text)


def clean(text: str) -> str:
    """De HTML a texto plano markdown-safe (entidades, itálicas simples)."""
    text = re.sub(r"</?(em|i)>", "*", text)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def frontmatter(d: dict) -> str:
    lines = ["---"]
    for k, v in d.items():
        if v is None:
            lines.append(f"{k}: null")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, list):
            lines.append(f"{k}: [{', '.join(json.dumps(x, ensure_ascii=False) for x in v)}]")
        elif isinstance(v, int):
            lines.append(f"{k}: {v}")
        else:
            lines.append(f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def write_md(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter(meta) + "\n\n" + body + "\n", encoding="utf-8")


def main() -> None:
    src = HTML_PATH.read_text(encoding="utf-8")
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    artistas_atlas = {a["slug"]: a for a in atlas["nodos"]["artistas"]}
    personas_atlas = {p["nombre"]: p["mbid"] for p in atlas["nodos"]["personas"] if p.get("nombre")}

    # Índice de release-groups por artista para el matching de álbumes.
    rgs_por_artista: dict[str, list[dict]] = {}
    for alb in atlas["nodos"]["albumes"]:
        rgs_por_artista.setdefault(alb["artist_slug"], []).append(alb)

    report = {"artistas": 0, "red": 0, "albumes": 0, "albumes_sin_mbid": [],
              "albumes_match_dudoso": [], "lineas_no_parseadas": []}

    # ---- secciones ----------------------------------------------------
    sec_artistas = src.split("<h2>Los artistas y sus etapas</h2>")[1].split("</section>")[0]
    sec_red = src.split("<h2>La red</h2>")[1].split("</section>")[0]
    sec_tiempo = src.split('<main id="tiempo">')[1].split("</main>")[0]

    # ---- 1. artistas ---------------------------------------------------
    for m in RE_BAND.finditer(sec_artistas):
        b, nombre, analisis = m.group("b"), clean(m.group("nombre")), clean(m.group("analisis"))
        if b == "npr":
            meta = {
                "tipo": "coleccion",
                "slug": "conceptuales-no-prog",
                "nombre": nombre,
                "grupo": "npr",
                "miembros": ["beatles", "pretty-things", "kinks", "small-faces"],
            }
            write_md(CONTENT / "artistas" / "conceptuales-no-prog.md", meta, analisis)
        else:
            art = artistas_atlas.get(b, {})
            meta = {
                "tipo": "artista",
                "slug": b,
                "nombre": nombre,
                "mbid": art.get("mbid"),
                "discogs_id": art.get("discogs_id"),
                "wikipedia_url": art.get("wikipedia_url"),
            }
            write_md(CONTENT / "artistas" / f"{b}.md", meta, analisis)
        report["artistas"] += 1

    # ---- 2. la red -----------------------------------------------------
    for m in RE_NODE.finditer(sec_red):
        tag, nombre, analisis = clean(m.group("tag")), clean(m.group("nombre")), clean(m.group("analisis"))
        tag_l = tag.lower()
        if "sello" in tag_l:
            tipo_nodo = "label"
        elif "estudio" in tag_l:
            tipo_nodo = "studio"
        else:
            tipo_nodo = "person"
        slug = slugify(nombre)
        meta = {
            "tipo": "red",
            "slug": slug,
            "nombre": nombre,
            "rol": tag,
            "tipo_nodo": tipo_nodo,
            "mbid": personas_atlas.get(nombre) if tipo_nodo == "person" else None,
        }
        write_md(CONTENT / "red" / f"{slug}.md", meta, analisis)
        report["red"] += 1

    # ---- 3. álbumes 1966-1980 -------------------------------------------
    year = None
    for line in sec_tiempo.splitlines():
        ym = RE_YEAR.search(line)
        if ym:
            y = ym.group("y")
            year = int(y) if re.fullmatch(r"\d{4}", y) else None  # None = continuación 81+
            continue
        if year is None or year > 1980:
            continue
        if "<article" in line:
            am = RE_ARTICLE.search(line)
            if not am:
                report["lineas_no_parseadas"].append(line.strip()[:120])
                continue
            b = am.group("b")
            # fichas compactadas llevan su año real tras el artista (« · 1971»)
            anio = int(am.group("anio_real")) if am.group("anio_real") else year
            titulo = clean(am.group("titulo"))
            artista = clean(am.group("artista"))
            analisis = clean(am.group("analisis"))
            charts = clean(am.group("charts"))
            aslug = NPR_EM_SLUG.get(artista.lower(), b) if b == "npr" else b

            # matching contra MusicBrainz
            candidatos = rgs_por_artista.get(aslug, [])
            dudoso = False
            manual = MANUAL_MATCHES.get((aslug, titulo))
            if manual:
                rg = next((c for c in candidatos if c["mbid"] == manual), None)
            else:
                sin_parentesis = re.sub(r"\s*\([^)]*\)", "", titulo)
                rg = None
                for objetivo in dict.fromkeys([norm_title(titulo), norm_title(sin_parentesis)]):
                    exactos = [c for c in candidatos if norm_title(c["titulo"] or "") == objetivo]
                    if not exactos:
                        exactos = [c for c in candidatos
                                   if objetivo and objetivo in norm_title(c["titulo"] or "")]
                        dudoso = bool(exactos)
                    if exactos:
                        exactos.sort(key=lambda c: (not c["es_estudio"], c["primer_lanzamiento"] or "9999"))
                        rg = exactos[0]
                        break

            slug = f"{aslug}-{slugify(titulo)}"
            estado = CHARTS_ESTADO.get(aslug, DEFAULT_ESTADO)
            meta = {
                "tipo": "album",
                "slug": slug,
                "titulo": titulo,
                "artista": artista,
                "artista_slug": aslug,
                "anio_ficha": anio,
                "mb_rgid": rg["mbid"] if rg else None,
                "primer_lanzamiento": rg["primer_lanzamiento"] if rg else None,
                "charts_texto": charts,
                "charts_estado": estado,
            }
            write_md(CONTENT / "albumes" / f"{slug}.md", meta, analisis)
            report["albumes"] += 1
            if not rg:
                report["albumes_sin_mbid"].append(f"{aslug}: {titulo} ({anio})")
            elif dudoso:
                report["albumes_match_dudoso"].append(
                    f"{aslug}: '{titulo}' -> '{rg['titulo']}' ({rg['mbid']})")

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[editorial] artistas: {report['artistas']}, red: {report['red']}, "
          f"álbumes: {report['albumes']}")
    print(f"[editorial] sin MBID: {len(report['albumes_sin_mbid'])}, "
          f"match dudoso: {len(report['albumes_match_dudoso'])}, "
          f"no parseadas: {len(report['lineas_no_parseadas'])}")
    for item in report["albumes_sin_mbid"]:
        print("   sin mbid:", item)
    for item in report["albumes_match_dudoso"]:
        print("   dudoso:  ", item)
    for item in report["lineas_no_parseadas"]:
        print("   no parse:", item)


if __name__ == "__main__":
    main()
