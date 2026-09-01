# Capa editorial — Fase 1, punto 2

Un markdown por nodo, migrado del prototipo `mapa-del-prog.html` con
`pipeline/migrate_editorial.py` (los MBIDs de la red, con `pipeline/resolve_red.py`).
El cuerpo de cada archivo es el análisis editorial **verbatim** del prototipo; el
frontmatter lleva los datos de enlace y el estado de verificación.

## Estructura

- `artistas/` — 26 fichas: 25 artistas con MBID/Discogs/Wikipedia + la colección
  `conceptuales-no-prog.md` (Beatles, Pretty Things, Kinks, Small Faces).
- `red/` — 20 nodos de la red (personas, sellos, estudios). 17 con MBID resuelto
  contra la API; los 3 compuestos (Charisma·Stratton-Smith, los cuatro estudios,
  Steve y John Hackett) quedan sin MBID único a propósito — separarlos es decisión
  del punto 3.
- `albumes/` — 208 fichas de la era clásica 1966–1980, cada una casada con su
  release-group de MusicBrainz (`mb_rgid`). Los 4 matches por título parcial están
  documentados en `data/editorial_report.json` y verificados a mano.

## `charts_estado` (regla editorial del brief)

El prototipo declara qué discografías fueron contrastadas con fuentes y cuáles siguen
escritas de memoria. Ese estado viaja en el frontmatter de cada álbum:

- `verificado` — King Crimson, Camel, Caravan, Jethro Tull, ELO, Rush, Strawbs, BJH.
- `parcial` — Gentle Giant (casi completo), Moody Blues (etapa central).
- `memoria` — todo lo demás. **Tratar como `s.d.` hasta verificar**: el sitio no debe
  presentar estos números como hechos.

Regenerar todo: `python3 pipeline/migrate_editorial.py && python3 pipeline/resolve_red.py`.
Ojo: regenerar pisa ediciones manuales de los `.md` — cuando la capa editorial empiece a
editarse a mano, el HTML deja de ser la fuente de verdad y estos scripts se congelan.
