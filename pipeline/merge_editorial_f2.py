#!/usr/bin/env python3
"""Aplica los resultados de los agentes (data/editorial_f2/*.json) a content/albumes/.

- excluir=true  -> borra la ficha md y registra en data/albumes_excluidos.json
- analisis      -> cuerpo del md (solo si estaba vacío)
- estrellas_critica / critica_nota -> frontmatter (critica_fuente: editorial)
- estrellas_comercial editorial    -> frontmatter solo si el script de charts no la puso

Lint final: ningún análisis nuevo puede contener posiciones de chart.

Uso:  python3 pipeline/merge_editorial_f2.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F2 = ROOT / "data" / "editorial_f2"
ALBUMES = ROOT / "content" / "albumes"
EXCLUIDOS_PATH = ROOT / "data" / "albumes_excluidos.json"

RE_CHART = re.compile(r"\b(?:UK|US)\s*[#nº]?\s*\d+|\bn[ºo°]\.?\s*\d+|\btop\s*\d+|Billboard\s*\d+", re.I)


def poner_campo(fm: str, k: str, v) -> str:
    val = "null" if v is None else (json.dumps(v, ensure_ascii=False) if isinstance(v, str) else v)
    if re.search(rf"^{k}:", fm, flags=re.M):
        return re.sub(rf"^{k}:.*$", f"{k}: {val}", fm, count=1, flags=re.M)
    return fm + f"{k}: {val}\n"


def main() -> None:
    excluidos, sin_md, lint, aplicados = [], [], [], 0
    for jpath in sorted(F2.glob("*.json")):
        data = json.loads(jpath.read_text(encoding="utf-8"))
        for a in data["albumes"]:
            slug = a["slug"]
            md = ALBUMES / f"{slug}.md"
            if not md.exists():
                sin_md.append(f"{jpath.stem}: {slug}")
                continue
            if a.get("excluir"):
                excluidos.append({"slug": slug, "motivo": a.get("motivo"), "fuente": jpath.stem})
                md.unlink()
                continue
            texto = md.read_text(encoding="utf-8")
            _, fm, cuerpo = texto.split("---\n", 2)

            analisis = a.get("analisis")
            if analisis and not cuerpo.strip():
                if RE_CHART.search(analisis):
                    lint.append(f"{slug}: «{RE_CHART.search(analisis).group(0)}»")
                cuerpo = "\n" + analisis.strip() + "\n"

            fm = poner_campo(fm, "estrellas_critica", a.get("estrellas_critica"))
            fm = poner_campo(fm, "critica_fuente", "editorial")
            if a.get("critica_nota"):
                fm = poner_campo(fm, "critica_nota", a["critica_nota"])
            if "estrellas_comercial:" not in fm and a.get("estrellas_comercial") is not None:
                fm = poner_campo(fm, "estrellas_comercial", a["estrellas_comercial"])
                fm = poner_campo(fm, "comercial_fuente", "editorial")
                if a.get("comercial_nota"):
                    fm = poner_campo(fm, "comercial_nota", a["comercial_nota"])
            md.write_text(f"---\n{fm}---\n{cuerpo}", encoding="utf-8")
            aplicados += 1

    EXCLUIDOS_PATH.write_text(json.dumps(excluidos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[merge] aplicados: {aplicados} · excluidos: {len(excluidos)} · sin md: {len(sin_md)}")
    for s in sin_md:
        print("   sin md:", s)
    if lint:
        print(f"[merge] LINT — análisis con datos de chart ({len(lint)}):")
        for s in lint:
            print("   ", s)
        sys.exit(1)

    # sanidad global: fichas sin estrellas de crítica
    faltan = [p.stem for p in ALBUMES.glob("*.md")
              if "estrellas_critica:" not in p.read_text(encoding="utf-8").split("---\n", 2)[1]]
    if faltan:
        print(f"[merge] fichas SIN estrellas_critica ({len(faltan)}): {faltan[:10]}{'…' if len(faltan) > 10 else ''}")


if __name__ == "__main__":
    main()
