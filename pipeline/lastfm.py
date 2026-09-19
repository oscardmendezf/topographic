#!/usr/bin/env python3
"""Capa de popularidad medida: las canciones más escuchadas de cada artista,
según Last.fm, ancladas al MBID que ya tiene el atlas.

La clave NO va en el repo. Se busca, en este orden:
  1. variable de entorno LASTFM_API_KEY
  2. ~/.config/atlas-prog/lastfm.key
  3. en CI, el secret LASTFM_API_KEY expuesto como variable de entorno

`artist.getTopTracks` acepta `mbid`, así que cada consulta va anclada al MBID
del atlas y no al nombre: es lo que evita el problema que descartó a Deezer,
donde «High Tide» resolvía a otro grupo. El servicio no requiere sesión de
usuario, solo la api_key.

Uso:
  python3 pipeline/lastfm.py cobertura [--muestra N]   # mide antes de escribir nada
  python3 pipeline/lastfm.py fetch                     # baja todo -> data/raw_lastfm/
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw_lastfm"
API = "https://ws.audioscrobbler.com/2.0/"
USER_AGENT = "AtlasDelProg/0.1 (pipeline local)"
RATE_SECONDS = 0.25          # la política de Last.fm pide no más de ~5 req/s por cuenta
LIMITE_TOP = 50

# Muestra deliberada: mezcla canónicos con las escenas más oscuras, que es
# donde la cobertura se cae y donde se decide si la capa vale la pena.
MUESTRA = ["yes", "pf", "kc", "gen", "hawkwind", "vanilla-fudge", "procol-harum",
           "spinetta", "seru-giran", "vox-dei", "los-jaivas", "os-mutantes",
           "bubu", "tantor", "high-tide", "third-ear-band", "quintessence",
           "silver-apples", "hp-lovecraft", "il-balletto-di-bronzo", "alas", "crucis"]

_ultimo = 0.0


def clave() -> str:
    k = os.environ.get("LASTFM_API_KEY", "").strip()
    if k:
        return k
    f = Path.home() / ".config" / "atlas-prog" / "lastfm.key"
    if f.exists():
        k = f.read_text(encoding="utf-8").strip()
        if k:
            return k
    sys.exit("[lastfm] falta la API key: exportá LASTFM_API_KEY o escribila en "
             "~/.config/atlas-prog/lastfm.key")


def api(metodo: str, **params) -> dict:
    global _ultimo
    q = urllib.parse.urlencode({"method": metodo, "api_key": clave(), "format": "json", **params})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": USER_AGENT})
    for intento in range(1, 5):
        espera = RATE_SECONDS - (time.monotonic() - _ultimo)
        if espera > 0:
            time.sleep(espera)
        _ultimo = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and intento < 4:
                time.sleep(2 * intento)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if intento < 4:
                time.sleep(2 * intento)
                continue
            raise
    raise RuntimeError(f"sin respuesta: {metodo}")


def top_tracks(mbid: str, nombre: str) -> list[dict]:
    """Por MBID; si Last.fm no lo conoce, reintenta por nombre y lo declara."""
    d = api("artist.getTopTracks", mbid=mbid, limit=LIMITE_TOP)
    tracks = (d.get("toptracks") or {}).get("track") or []
    por = "mbid"
    if not tracks:
        d = api("artist.getTopTracks", artist=nombre, limit=LIMITE_TOP, autocorrect=0)
        tracks = (d.get("toptracks") or {}).get("track") or []
        por = "nombre" if tracks else "—"
    return [{"titulo": t.get("name"), "mbid": t.get("mbid") or None,
             "playcount": int(t.get("playcount") or 0),
             "listeners": int(t.get("listeners") or 0), "resuelto_por": por}
            for t in tracks]


def artistas() -> dict:
    atlas = json.loads((DATA / "atlas.json").read_text(encoding="utf-8"))
    return {a["slug"]: a for a in atlas["nodos"]["artistas"]}


def cmd_cobertura() -> None:
    n = int(sys.argv[sys.argv.index("--muestra") + 1]) if "--muestra" in sys.argv else len(MUESTRA)
    art = artistas()
    seed = {s["slug"]: s for s in json.loads(
        (ROOT / "pipeline" / "artists_seed.json").read_text(encoding="utf-8"))["artistas"]}
    print(f"{'artista':26s} {'escena':14s} {'tracks':>6s} {'con mbid':>9s} {'oyentes máx':>12s}  resuelto")
    print("-" * 82)
    filas = []
    for slug in MUESTRA[:n]:
        a = art.get(slug)
        if not a:
            print(f"{slug:26s} (no está en el atlas)")
            continue
        try:
            ts = top_tracks(a["mbid"], a["nombre"])
        except Exception as e:
            print(f"{slug:26s} ERROR {type(e).__name__}: {e}")
            continue
        con_mbid = sum(1 for t in ts if t["mbid"])
        top = max((t["listeners"] for t in ts), default=0)
        modo = ts[0]["resuelto_por"] if ts else "—"
        esc = (seed.get(slug, {}).get("escena") or "nucleo")[:14]
        print(f"{slug:26s} {esc:14s} {len(ts):6d} {con_mbid:9d} {top:12,d}  {modo}")
        filas.append((slug, esc, len(ts), con_mbid, top))
    if filas:
        vacios = [f[0] for f in filas if f[2] == 0]
        pobres = [f[0] for f in filas if 0 < f[4] < 1000]
        print("-" * 82)
        print(f"artistas sin ningún track: {len(vacios)}/{len(filas)} {vacios or ''}")
        print(f"artistas con menos de 1000 oyentes en su pico: {len(pobres)} {pobres or ''}")
        print(f"tracks con MBID propio: {sum(f[3] for f in filas)}/{sum(f[2] for f in filas)}"
              "  (los que se pueden cruzar sin adivinar por título)")


def cmd_fetch() -> None:
    RAW.mkdir(exist_ok=True)
    art = artistas()
    hechos = 0
    for slug, a in sorted(art.items()):
        destino = RAW / f"{slug}.json"
        if destino.exists():
            continue
        ts = top_tracks(a["mbid"], a["nombre"])
        destino.write_text(json.dumps(
            {"slug": slug, "mbid": a["mbid"], "nombre": a["nombre"],
             "capturado": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
             "fuente": "last.fm artist.getTopTracks", "tracks": ts},
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        hechos += 1
        if hechos % 20 == 0:
            print(f"[lastfm] {hechos} artistas")
    print(f"[lastfm] listo: {hechos} artistas nuevos en {RAW.relative_to(ROOT)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "cobertura"
    {"cobertura": cmd_cobertura, "fetch": cmd_fetch}.get(cmd, cmd_cobertura)()
