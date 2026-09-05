# Pipeline MusicBrainz — Fase 1, punto 1

Baja el universo del prototipo (`mapa-del-prog.html`) desde la API de MusicBrainz y lo
normaliza al modelo de datos del brief. Solo stdlib de Python 3; sin dependencias.

## Uso

```sh
python3 pipeline/musicbrainz.py resolve    # busca MBIDs por nombre -> data/mbid_map.json
python3 pipeline/musicbrainz.py fetch      # baja artista + release-groups + wikidata -> data/raw/<slug>/
python3 pipeline/musicbrainz.py normalize  # arma el grafo -> data/atlas.json
python3 pipeline/musicbrainz.py all
```

Cada paso es reanudable: `fetch` salta lo que ya existe en `data/raw/`. Para refrescar
un artista, borrar su carpeta en `data/raw/` y volver a correr `fetch`.

## Los «26 artistas»

El prototipo cuenta 26 porque agrupa a los conceptuales no-prog (Beatles, Pretty Things,
Kinks, Small Faces) como una sola entrada junto a las 25 bandas con chip propio. Como
entidades de MusicBrainz son **29**, definidas en `artists_seed.json` (slugs = códigos
`data-b` del HTML; los no-prog llevan `grupo: "npr"`).

## Reglas que implementa (del brief)

- **Ningún MBID de memoria**: `resolve` busca por nombre en la API, puntúa candidatos con
  los hints del seed (tipo, país, texto de desambiguación) y marca `revisar` cualquier
  match dudoso; `fetch` no baja nada que no esté en `ok`.
- **Rate limit**: 1 request/seg (política de MusicBrainz), con reintentos y backoff en
  429/503, también contra Wikidata.
- **Verificabilidad delegada**: cada nodo artista sale con `mbid`, `discogs_id` (derivado
  del url-rel de Discogs) y `wikipedia_url` (sitelink de Wikidata, es > en).

## Salidas

- `data/mbid_map.json` — resolución nombre→MBID con score y alternativas.
- `data/raw/<slug>/artist.json` — respuesta cruda con `artist-rels` (miembros) y `url-rels`.
- `data/raw/<slug>/release-groups.json` — todos los release-groups tipo álbum.
- `data/raw/<slug>/wikidata.json` — sitelinks eswiki/enwiki.
- `data/atlas.json` — el grafo: nodos (`artistas`, `personas`, `albumes`) y aristas
  (`member_of` con rangos temporales y roles/instrumentos). Los campos `analisis_md`
  quedan en `null`: los llena la capa editorial (Fase 1, punto 2).

## Historias largas por álbum (04-sep-2026)

Cada ficha de álbum lleva, tras la entradilla original, tres secciones editoriales
(`## La historia`, `## La producción`, `## Recepción y legado`) separadas por el marcador
`<!-- historia:editorial -->` y declaradas en el frontmatter con `historia: editorial`.

- `build_tareas_historias.py [lote]` → `data/tareas_historias.json` + un archivo por grupo en
  `data/tareas_historias/` con las anclas verificadas (tracklist, créditos de MB, fecha, análisis).
  Las instrucciones para los redactores están en `data/tareas_historias/INSTRUCCIONES.md`.
- Los redactores escriben un JSON por álbum en `data/editorial_historias/partes/<grupo>/<slug>.json`
  (o un JSON por grupo en `data/editorial_historias/`).
- `estado_historias.py` → escritas vs. pendientes por grupo.
- `merge_historias.py [--check]` → aplica las historias a `content/albumes/*.md`. Lint (sale ≠0 y no
  aplica la historia): posiciones de chart, ventas, certificaciones, fechas completas, secciones faltantes.
  Re-ejecutar reemplaza la historia sin tocar la entradilla.
