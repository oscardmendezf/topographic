#!/usr/bin/env python3
"""Analiza los créditos crudos (data/raw_credits/) para:

1. data/creditos.json — créditos normalizados por álbum y agregados por artista.
2. data/red_verificacion.json — qué aristas curadas de la red quedan VERIFICADAS
   por los créditos de MusicBrainz (con evidencia: en qué álbumes).
3. Reporte de descubrimiento: personas que aparecen en créditos de ≥3 álbumes
   de ≥2 artistas del universo y no son nodos de la red -> candidatos a nodo.

Uso:  python3 pipeline/build_credits.py
"""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw_credits"
ALBUMES = ROOT / "content" / "albumes"
RED = ROOT / "content" / "red"

ROLES = {
    "produced": {"producer", "co-producer", "executive producer"},
    "engineered": {"engineer", "audio", "mix", "recording", "mastering", "sound"},
    "arranged": {"arranger", "orchestrator", "instrument arranger", "vocal arranger", "orchestration"},
    "designed_artwork": {"design/illustration", "design", "illustration", "graphic design", "photography", "art direction"},
    "wrote_lyrics": {"lyricist"},
    "guested_on": {"instrument", "vocal", "performer", "performing orchestra"},
    "member_of": set(),  # se verifica por otra vía (ya viene del atlas)
}
ESTUDIOS_COMPUESTO = {"advision": "Advision", "trident": "Trident", "abbey road": "Abbey Road", "manor": "The Manor"}


def frontmatter(path: Path) -> dict:
    fm = path.read_text(encoding="utf-8").split("---\n", 2)[1]
    out = {}
    for k in ("slug", "artista_slug", "mbid", "mb_label_id", "titulo"):
        m = re.search(rf'^{k}: "(.*)"$', fm, flags=re.M)
        if m:
            out[k] = m.group(1)
    return out


def main() -> None:
    artista_de, titulo_de = {}, {}
    for p in ALBUMES.glob("*.md"):
        fm = frontmatter(p)
        artista_de[p.stem] = fm.get("artista_slug")
        titulo_de[p.stem] = fm.get("titulo", p.stem)

    por_album, por_artista = {}, defaultdict(lambda: defaultdict(lambda: {"roles": set(), "albumes": set(), "nombre": None}))
    sellos_por_artista = defaultdict(lambda: defaultdict(set))
    lugares_por_artista = defaultdict(lambda: defaultdict(set))

    for p in sorted(RAW.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("sin_release"):
            continue
        slug = d["album_slug"]
        aslug = artista_de.get(slug)
        if not aslug:
            continue
        por_album[slug] = d
        for li in d.get("labels", []):
            if li.get("mbid"):
                sellos_por_artista[aslug][li["mbid"]].add(slug)
        for r in d.get("rels", []):
            if not r.get("mbid"):
                continue
            if r["target"] == "place":
                lugares_por_artista[aslug][(r["mbid"], r["nombre"] or "")].add(slug)
            else:
                ent = por_artista[aslug][r["mbid"]]
                ent["nombre"] = r["nombre"]
                ent["roles"].add((r.get("tipo") or "").lower())
                ent["albumes"].add(slug)

    # ---- verificación de aristas curadas --------------------------------
    red_meta = {}
    for p in RED.glob("*.md"):
        red_meta[p.stem] = frontmatter(p)
    curadas = json.loads((ROOT / "pipeline" / "red_edges.json").read_text(encoding="utf-8"))["aristas"]

    verif = {}
    for e in curadas:
        clave = f"{e['red']}|{e['artista']}|{e['tipo']}"
        meta = red_meta.get(e["red"], {})
        tipo = e["tipo"]
        resultado = {"verificado": False, "evidencia": []}

        if tipo == "signed_to" and meta.get("mb_label_id"):
            albs = sellos_por_artista.get(e["artista"], {}).get(meta["mb_label_id"], set())
            if albs:
                resultado = {"verificado": True, "evidencia": sorted(titulo_de[a] for a in albs)[:6], "via": "sello del release"}
        elif tipo == "recorded_at" and e["red"].startswith("advision"):
            objetivo = ESTUDIOS_COMPUESTO.get(e["etiqueta"].lower().strip(), e["etiqueta"])
            albs = set()
            for (mbid, nombre), aa in lugares_por_artista.get(e["artista"], {}).items():
                if objetivo.lower() in (nombre or "").lower():
                    albs |= aa
            if albs:
                resultado = {"verificado": True, "evidencia": sorted(titulo_de[a] for a in albs)[:6], "via": "place-rel del release"}
        elif meta.get("mbid"):
            ent = por_artista.get(e["artista"], {}).get(meta["mbid"])
            if ent:
                roles_ok = ROLES.get(tipo, set())
                if not roles_ok or any(any(rr in rol for rr in roles_ok) for rol in ent["roles"]):
                    resultado = {"verificado": True,
                                 "evidencia": sorted(titulo_de[a] for a in ent["albumes"])[:6],
                                 "via": f"rels: {', '.join(sorted(ent['roles']))[:80]}"}
        verif[clave] = {**resultado, "etiqueta": e["etiqueta"]}

    n_ok = sum(1 for v in verif.values() if v["verificado"])
    (ROOT / "data" / "red_verificacion.json").write_text(
        json.dumps(verif, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # ---- descubrimiento de conectores ------------------------------------
    mbids_red = {m.get("mbid") for m in red_meta.values()} | {m.get("mb_label_id") for m in red_meta.values()}
    atlas = json.loads((ROOT / "data" / "atlas.json").read_text(encoding="utf-8"))
    mbids_universo = {a["mbid"] for a in atlas["nodos"]["artistas"]}
    mbids_personas_univ = {p["mbid"] for p in atlas["nodos"]["personas"]}

    global_por_persona = defaultdict(lambda: {"nombre": None, "artistas": set(), "albumes": set(), "roles": set()})
    for aslug, personas in por_artista.items():
        for mbid, ent in personas.items():
            if mbid in mbids_red or mbid in mbids_universo:
                continue
            g = global_por_persona[mbid]
            g["nombre"] = ent["nombre"]
            g["artistas"].add(aslug)
            g["albumes"] |= ent["albumes"]
            g["roles"] |= ent["roles"]

    candidatos = [
        {"mbid": m, "nombre": g["nombre"], "artistas": sorted(g["artistas"]),
         "n_albumes": len(g["albumes"]), "roles": sorted(g["roles"])[:6],
         "es_musico_universo": m in mbids_personas_univ}
        for m, g in global_por_persona.items()
        if len(g["artistas"]) >= 2 and len(g["albumes"]) >= 3
    ]
    candidatos.sort(key=lambda c: (-len(c["artistas"]), -c["n_albumes"]))
    (ROOT / "data" / "red_candidatos.json").write_text(
        json.dumps(candidatos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    creditos_min = {s: {"labels": d.get("labels", []), "rels": d.get("rels", [])} for s, d in por_album.items()}
    (ROOT / "data" / "creditos.json").write_text(json.dumps(creditos_min, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[creditos] álbumes con créditos: {len(por_album)}")
    print(f"[creditos] aristas curadas verificadas: {n_ok}/{len(verif)}")
    for k, v in verif.items():
        marca = "✓" if v["verificado"] else "✗"
        print(f"   {marca} {k}" + (f"  ({v.get('via','')})" if v["verificado"] else ""))
    print(f"[creditos] candidatos a nodo nuevo (≥2 artistas, ≥3 álbumes): {len(candidatos)} — top 15:")
    for c in candidatos[:15]:
        extra = " [músico del universo]" if c["es_musico_universo"] else ""
        print(f"   {c['nombre']}: {len(c['artistas'])} artistas, {c['n_albumes']} álbumes — {', '.join(c['artistas'][:6])}{extra}")


if __name__ == "__main__":
    main()
