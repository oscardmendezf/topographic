#!/usr/bin/env python3
"""Geolocalización de artistas vía Wikidata (cero datos de memoria).

Para cada artista del atlas: toma su QID (data/raw/<slug>/wikidata.json),
consulta P740 (lugar de formación) para grupos o P19 (lugar de nacimiento)
para personas, y luego las coordenadas P625 del lugar. Batches de 50 QIDs.

Salida: data/geo.json  {slug: {lugar, lugar_qid, lat, lon, propiedad}}
Sin lugar o sin coordenadas -> el artista queda fuera del mapa, declarado.

Uso:  python3 pipeline/geo.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from musicbrainz import RAW_DIR, ATLAS_PATH, fetch_url_json

GEO_PATH = Path(__file__).resolve().parent.parent / "data" / "geo.json"
API = "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"


def batched(ids: list[str], n: int = 50):
    for i in range(0, len(ids), n):
        yield ids[i:i + n]


def get_entities(qids: list[str], props: str) -> dict:
    out = {}
    for lote in batched(sorted(set(qids))):
        res = fetch_url_json(f"{API}&ids={'|'.join(lote)}&props={props}")
        out.update(res.get("entities", {}))
    return out


def area_wikidata(slug: str):
    """QID del begin-area del artista según MusicBrainz (área -> url-rel wikidata)."""
    from musicbrainz import api_get
    raw = RAW_DIR / slug / "artist.json"
    if not raw.exists():
        return None
    artist = json.loads(raw.read_text(encoding="utf-8"))
    area = artist.get("begin-area") or artist.get("area")
    if not area or not area.get("id"):
        return None
    detalle = api_get(f"area/{area['id']}", {"inc": "url-rels"})
    for rel in detalle.get("relations", []):
        url = rel.get("url", {}).get("resource", "")
        if "wikidata.org" in url:
            return url.rstrip("/").rsplit("/", 1)[-1]
    return None


def primer_claim(ent: dict, prop: str):
    claims = ent.get("claims", {}).get(prop, [])
    for c in claims:
        val = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if val:
            return val
    return None


def main() -> None:
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    artistas = atlas["nodos"]["artistas"]

    qid_de = {}
    for a in artistas:
        wd = RAW_DIR / a["slug"] / "wikidata.json"
        if wd.exists():
            qid = json.loads(wd.read_text(encoding="utf-8")).get("qid")
            if qid:
                qid_de[a["slug"]] = qid

    ents = get_entities(list(qid_de.values()), "claims")
    lugares, eleccion = set(), {}
    for a in artistas:
        qid = qid_de.get(a["slug"])
        ent = ents.get(qid, {}) if qid else {}
        prop = "P740" if a["tipo"] == "Group" else "P19"
        val = primer_claim(ent, prop) or primer_claim(ent, "P740" if prop == "P19" else "P19")
        if val and isinstance(val, dict) and val.get("id"):
            eleccion[a["slug"]] = {"lugar_qid": val["id"], "propiedad": prop}
            lugares.add(val["id"])
            continue
        # Fallback: begin-area de MusicBrainz -> QID del área vía sus url-rels.
        qid_area = area_wikidata(a["slug"])
        if qid_area:
            eleccion[a["slug"]] = {"lugar_qid": qid_area, "propiedad": "mb:begin-area"}
            lugares.add(qid_area)
        else:
            print(f"[geo] {a['slug']}: sin lugar en Wikidata ni begin-area MB (fuera del mapa)")

    ents_lugar = get_entities(list(lugares), "claims|labels")
    geo = {}
    for slug, e in eleccion.items():
        ent = ents_lugar.get(e["lugar_qid"], {})
        coord = primer_claim(ent, "P625")
        labels = ent.get("labels", {})
        nombre = (labels.get("es") or labels.get("en") or {}).get("value")
        if coord and "latitude" in coord:
            geo[slug] = {
                "lugar": nombre,
                "lugar_qid": e["lugar_qid"],
                "lat": round(coord["latitude"], 4),
                "lon": round(coord["longitude"], 4),
                "propiedad": e["propiedad"],
            }
        else:
            print(f"[geo] {slug}: lugar {nombre or e['lugar_qid']} sin coordenadas P625")

    GEO_PATH.write_text(json.dumps(geo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[geo] geolocalizados: {len(geo)}/{len(artistas)}")


if __name__ == "__main__":
    main()
