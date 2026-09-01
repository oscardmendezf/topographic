#!/usr/bin/env python3
"""Atlas del Prog — Fase 1, punto 1: pipeline MusicBrainz.

Tres pasos, cada uno reanudable:

  python3 pipeline/musicbrainz.py resolve    # busca cada artista del seed y fija su MBID -> data/mbid_map.json
  python3 pipeline/musicbrainz.py fetch      # baja artista (miembros + urls) y release-groups -> data/raw/<slug>/
  python3 pipeline/musicbrainz.py normalize  # arma el grafo (nodos + aristas) -> data/atlas.json
  python3 pipeline/musicbrainz.py all

Reglas: ningún MBID escrito de memoria (todo sale de la API de búsqueda);
1 request/segundo según la política de MusicBrainz; los matches dudosos
quedan marcados "revisar" en mbid_map.json y no se bajan hasta confirmarlos.
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://musicbrainz.org/ws/2"
USER_AGENT = "AtlasDelProg/0.1 (pipeline local, Fase 1)"
RATE_SECONDS = 1.1
RETRIES = 5

ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "pipeline" / "artists_seed.json"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MAP_PATH = DATA_DIR / "mbid_map.json"
ATLAS_PATH = DATA_DIR / "atlas.json"

_last_request = 0.0


def api_get(path: str, params: dict) -> dict:
    """GET con rate-limit global y reintentos ante 503/red."""
    global _last_request
    query = urllib.parse.urlencode({**params, "fmt": "json"})
    url = f"{BASE}/{path}?{query}"
    for attempt in range(1, RETRIES + 1):
        wait = RATE_SECONDS - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < RETRIES:
                time.sleep(2 * attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < RETRIES:
                time.sleep(2 * attempt)
                continue
            raise
    raise RuntimeError(f"sin respuesta tras {RETRIES} intentos: {url}")


def fetch_url_json(url: str) -> dict:
    """GET genérico (Wikidata) con el mismo rate-limit y reintentos."""
    global _last_request
    for attempt in range(1, RETRIES + 1):
        wait = RATE_SECONDS - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < RETRIES:
                retry_after = e.headers.get("Retry-After")
                time.sleep(int(retry_after) if retry_after and retry_after.isdigit() else 5 * attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < RETRIES:
                time.sleep(2 * attempt)
                continue
            raise
    raise RuntimeError(f"sin respuesta tras {RETRIES} intentos: {url}")


def load_seed() -> list[dict]:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))["artistas"]


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- resolve

def score_candidate(seed: dict, cand: dict) -> int:
    """Puntaje = score de MusicBrainz + bonos por coincidir con los hints del seed."""
    score = cand.get("score", 0)
    if cand.get("name", "").lower() == seed["name"].lower():
        score += 15
    if seed.get("country") and cand.get("country") == seed["country"]:
        score += 10
    hint = seed.get("disambiguation_hint")
    if hint and hint.lower() in (cand.get("disambiguation") or "").lower():
        score += 20
    return score


def cmd_resolve() -> None:
    seeds = load_seed()
    out = {}
    for seed in seeds:
        lucene = f'artist:"{seed["name"]}"'
        if seed.get("type"):
            lucene += f' AND type:{seed["type"].lower()}'
        res = api_get("artist", {"query": lucene, "limit": 10})
        candidates = [
            c for c in res.get("artists", [])
            if not seed.get("type") or (c.get("type") or "").lower() == seed["type"].lower()
        ]
        ranked = sorted(candidates, key=lambda c: score_candidate(seed, c), reverse=True)
        if not ranked:
            out[seed["slug"]] = {"name": seed["name"], "status": "sin_resultados"}
            print(f"[resolve] {seed['slug']:14s} SIN RESULTADOS")
            continue
        best = ranked[0]
        best_score = score_candidate(seed, best)
        runner_up = score_candidate(seed, ranked[1]) if len(ranked) > 1 else -999
        status = "ok" if best.get("score", 0) >= 90 and best_score - runner_up >= 10 else "revisar"
        out[seed["slug"]] = {
            "name": seed["name"],
            "mbid": best["id"],
            "mb_name": best.get("name"),
            "type": best.get("type"),
            "country": best.get("country"),
            "disambiguation": best.get("disambiguation", ""),
            "mb_score": best.get("score"),
            "status": status,
            "alternativas": [
                {
                    "mbid": c["id"],
                    "mb_name": c.get("name"),
                    "country": c.get("country"),
                    "disambiguation": c.get("disambiguation", ""),
                    "mb_score": c.get("score"),
                }
                for c in ranked[1:4]
            ] if status == "revisar" else [],
        }
        print(f"[resolve] {seed['slug']:14s} {status:8s} {best['id']}  {best.get('name')}"
              f"  ({best.get('disambiguation', '') or 'sin desambiguación'})")
    write_json(MAP_PATH, {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente": "búsqueda API MusicBrainz (ningún MBID de memoria)",
        "artistas": out,
    })
    pendientes = [s for s, v in out.items() if v.get("status") != "ok"]
    print(f"\n[resolve] {len(out)} artistas, {len(pendientes)} a revisar: {pendientes or '—'}")


# ---------------------------------------------------------------- fetch

def cmd_fetch() -> None:
    mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))["artistas"]
    saltados = []
    for slug, entry in mapping.items():
        if entry.get("status") != "ok":
            saltados.append(slug)
            continue
        mbid = entry["mbid"]
        artist_path = RAW_DIR / slug / "artist.json"
        rg_path = RAW_DIR / slug / "release-groups.json"

        if not artist_path.exists():
            artist = api_get(f"artist/{mbid}", {"inc": "artist-rels+url-rels+aliases"})
            write_json(artist_path, artist)
            print(f"[fetch] {slug:14s} artista: {artist.get('name')} "
                  f"({len(artist.get('relations', []))} relaciones)")

        if not rg_path.exists():
            groups, offset = [], 0
            while True:
                page = api_get("release-group", {
                    "artist": mbid, "type": "album", "limit": 100, "offset": offset,
                })
                groups.extend(page.get("release-groups", []))
                total = page.get("release-group-count", len(groups))
                offset += 100
                if len(groups) >= total:
                    break
            write_json(rg_path, {"release-group-count": len(groups), "release-groups": groups})
            print(f"[fetch] {slug:14s} release-groups: {len(groups)}")

        wd_path = RAW_DIR / slug / "wikidata.json"
        if not wd_path.exists():
            artist = json.loads(artist_path.read_text(encoding="utf-8"))
            wd_url = extract_links(artist.get("relations", [])).get("wikidata")
            if wd_url:
                qid = wd_url.rstrip("/").rsplit("/", 1)[-1]
                res = fetch_url_json(
                    "https://www.wikidata.org/w/api.php?action=wbgetentities"
                    f"&ids={qid}&props=sitelinks%2Furls&sitefilter=eswiki%7Cenwiki&format=json"
                )
                sitelinks = res.get("entities", {}).get(qid, {}).get("sitelinks", {})
                write_json(wd_path, {"qid": qid, "sitelinks": sitelinks})
                print(f"[fetch] {slug:14s} wikidata {qid}: {sorted(sitelinks)}")
            else:
                write_json(wd_path, {"qid": None, "sitelinks": {}})
    if saltados:
        print(f"\n[fetch] saltados por status != ok: {saltados}")


# ---------------------------------------------------------------- normalize

LINK_HOSTS = {
    "discogs": "discogs.com",
    "wikidata": "wikidata.org",
    "wikipedia": "wikipedia.org",
}


def extract_links(relations: list[dict]) -> dict:
    links = {}
    for rel in relations:
        if rel.get("target-type") != "url":
            continue
        url = rel.get("url", {}).get("resource", "")
        for key, host in LINK_HOSTS.items():
            if host in url and key not in links:
                links[key] = url
    return links


def cmd_normalize() -> None:
    mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))["artistas"]
    seeds = {s["slug"]: s for s in load_seed()}
    artistas, personas, albumes, member_of = [], {}, [], []

    for slug, entry in mapping.items():
        artist_path = RAW_DIR / slug / "artist.json"
        rg_path = RAW_DIR / slug / "release-groups.json"
        if not artist_path.exists() or not rg_path.exists():
            print(f"[normalize] {slug}: sin datos crudos, se omite")
            continue
        artist = json.loads(artist_path.read_text(encoding="utf-8"))
        rgs = json.loads(rg_path.read_text(encoding="utf-8"))["release-groups"]
        relations = artist.get("relations", [])
        links = extract_links(relations)
        discogs_id = None
        if "discogs" in links:
            resto = links["discogs"].rstrip("/").rsplit("/", 1)[-1]
            discogs_id = resto.split("-")[0] if resto.split("-")[0].isdigit() else None

        wikipedia_url = links.get("wikipedia")
        wd_path = RAW_DIR / slug / "wikidata.json"
        if not wikipedia_url and wd_path.exists():
            sitelinks = json.loads(wd_path.read_text(encoding="utf-8")).get("sitelinks", {})
            for site in ("eswiki", "enwiki"):
                if site in sitelinks and sitelinks[site].get("url"):
                    wikipedia_url = sitelinks[site]["url"]
                    break

        artistas.append({
            "slug": slug,
            "mbid": artist["id"],
            "nombre": artist.get("name"),
            "tipo": artist.get("type"),
            "pais": artist.get("country"),
            "inicio": (artist.get("life-span") or {}).get("begin"),
            "fin": (artist.get("life-span") or {}).get("end"),
            "grupo": seeds.get(slug, {}).get("grupo"),
            "links": links,
            "discogs_id": discogs_id,
            "wikipedia_url": wikipedia_url,
            "analisis_md": None,
        })

        for rel in relations:
            if rel.get("type") != "member of band" or rel.get("target-type") != "artist":
                continue
            person = rel.get("artist", {})
            pid = person.get("id")
            if not pid:
                continue
            personas.setdefault(pid, {
                "mbid": pid,
                "nombre": person.get("name"),
                "tipo": person.get("type"),
                "analisis_md": None,
            })
            member_of.append({
                "person_mbid": pid,
                "person_nombre": person.get("name"),
                "artist_slug": slug,
                "artist_mbid": artist["id"],
                "desde": rel.get("begin"),
                "hasta": rel.get("end"),
                "vigente": not rel.get("ended", False),
                "roles": rel.get("attributes", []),
            })

        for rg in rgs:
            albumes.append({
                "mbid": rg["id"],
                "titulo": rg.get("title"),
                "artist_slug": slug,
                "primer_lanzamiento": rg.get("first-release-date") or None,
                "tipo_primario": rg.get("primary-type"),
                "tipos_secundarios": rg.get("secondary-types", []),
                "es_estudio": not rg.get("secondary-types"),
                "analisis_md": None,
            })

    atlas = {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente": "MusicBrainz (https://musicbrainz.org), licencia de datos CC0/CC BY-NC-SA",
        "fase": 1,
        "nodos": {
            "artistas": artistas,
            "personas": sorted(personas.values(), key=lambda p: p["nombre"] or ""),
            "albumes": sorted(albumes, key=lambda a: (a["primer_lanzamiento"] or "9999", a["titulo"] or "")),
        },
        "aristas": {
            "member_of": member_of,
        },
    }
    write_json(ATLAS_PATH, atlas)
    estudio = sum(1 for a in albumes if a["es_estudio"])
    print(f"[normalize] atlas.json: {len(artistas)} artistas, {len(personas)} personas, "
          f"{len(albumes)} release-groups ({estudio} de estudio), {len(member_of)} membresías")


# ---------------------------------------------------------------- main

def main() -> None:
    cmds = {"resolve": cmd_resolve, "fetch": cmd_fetch, "normalize": cmd_normalize}
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "all":
        for fn in cmds.values():
            fn()
    elif arg in cmds:
        cmds[arg]()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
