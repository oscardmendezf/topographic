#!/usr/bin/env python3
"""Estado de las historias por grupo: escritas vs. pendientes."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data" / "editorial_historias"
hechos = set()
for p in D.glob("*.json"):
    for a in json.loads(p.read_text())["albumes"]:
        hechos.add(a["album_slug"])
for p in D.glob("partes/*/*.json"):
    hechos.add(json.loads(p.read_text())["album_slug"])
tot = falt = 0
for g in sorted((ROOT / "data" / "tareas_historias").glob("his-*.json")):
    albs = [a["album_slug"] for a in json.loads(g.read_text())["albumes"]]
    pend = [s for s in albs if s not in hechos]
    tot += len(albs); falt += len(pend)
    if pend:
        print(f"{g.stem}: {len(albs)-len(pend)}/{len(albs)}  faltan {len(pend)}")
print(f"TOTAL escritas {tot-falt}/{tot}")
