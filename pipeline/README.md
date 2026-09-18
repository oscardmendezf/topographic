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

## Ampliar una escena con artistas nuevos (receta, usada en Argentina 09-sep-2026)

1. Agregar los artistas a `artists_seed.json` (`grupo`/`escena`, `fase`, `type`, `country`,
   `disambiguation_hint` si el nombre es ambiguo).
2. `musicbrainz.py resolve` (re-resuelve todo; ~1 s por artista; revisar que los previos no
   cambien de MBID) → `fetch` (solo baja lo nuevo) → `normalize`.
3. `build_tareas_escena.py <nombre>` (grupos en `CONFIG`) → `data/tareas_<nombre>/<grupo>.json`
   con catálogo de estudio, `formaciones_mb` y enlaces. Instrucciones para redactores en
   `data/tareas_<nombre>/INSTRUCCIONES.md`.
4. Redactores → `data/editorial_<nombre>/<grupo>.json` (ficha larga de artista, entradilla y
   estrellas por álbum, `excluidos` con motivo). `merge_f3.py <nombre> --check` verifica lint
   y cobertura del catálogo; sin `--check` escribe `content/` y registra exclusiones.
5. `fetch_credits.py` → `fetch_tracklists.py` → `build_credits.py` → `build_tracklists.py`;
   `geo.py`; `build_grafo.py`; `audit_cobertura.py`.
6. Historias largas: `build_tareas_historias.py 12 --pendientes --prefijo=his-xx` genera solo
   los grupos de álbumes sin historia (no pisa el manifiesto principal) → redactores →
   `merge_historias.py`.

## Fichas largas de artista — «el copy» (18-sep-2026)

Las fichas de artista del núcleo y de las escenas F3/Américas eran entradillas de 2–4 líneas
heredadas del prototipo; solo los 17 argentinos de F7 tenían ficha larga. Ahora los 104
artistas llevan ficha larga (320–450 palabras, 3–5 párrafos, sin títulos) **debajo** de la
entradilla original, separada por el marcador `<!-- copy:editorial -->` y declarada en el
frontmatter con `copy: editorial`. La ficha muestra el badge «ficha editorial».

- `build_tareas_copys.py [--todos] [--lote N] [--escena X]` → `data/tareas_copys/<grupo>.json`
  con las anclas verificadas: entradilla actual, `formaciones_mb`, discografía publicada (año,
  estrellas y entradilla de cada disco), conexiones de la red y vecinos de escena. Por defecto
  solo arma lotes con los artistas que **no** tienen ficha larga. Instrucciones para los
  redactores en `data/tareas_copys/INSTRUCCIONES.md`.
- Los redactores escriben `data/editorial_copys/<grupo>.json` con `{"artistas":[{"slug","copy_md"}]}`.
- `merge_copys.py [--check]` → aplica al cuerpo de `content/artistas/*.md`. Lint (sale ≠0 y no
  aplica esa ficha): posiciones de chart, ventas, certificaciones, fechas completas, títulos
  markdown y fichas de menos de 200 palabras. Re-ejecutar reemplaza la ficha sin tocar la
  entradilla.
- El bloque no-prog comparte una sola ficha (`conceptuales-no-prog`), que no está en el atlas:
  su lote se arma a mano (ver `data/tareas_copys/copy-16-npr.json`).

## Escena «Rarezas» — psicodelia → prog (18-sep-2026)

22 artistas de psicodelia y proto-prog (1966–1972) que son el eslabón anterior al género:
The Nice, Procol Harum, The Crazy World of Arthur Brown, Traffic, Family, Tomorrow,
Kaleidoscope UK, Nirvana UK, The Zombies, Third Ear Band, High Tide, Quintessence, Hawkwind,
Vanilla Fudge, Iron Butterfly, Spirit, The Electric Prunes, The United States of America,
Silver Apples, H.P. Lovecraft, Captain Beefheart & His Magic Band y Aphrodite's Child.
Escena `rarezas`, fase 8; 180 fichas de álbum y 19 exclusiones; charts siempre `s.d.`
(no hay fuente para esta pasada). Se armó con la receta «Ampliar una escena»
(`build_tareas_escena.py rarezas` → redactores → `merge_f3.py rarezas`).

`nirvana-uk` quedó en `revisar` tras `resolve` porque el grupo de Seattle puntúa más alto;
se confirmó a mano en `data/mbid_map.json` con la desambiguación de MusicBrainz
(`60s band from the UK`, país GB) y el campo `confirmado_a_mano`.

### Trampa conocida del lint

`RE_DURO` incluye `\bcertific`, así que verbos comunes como «certifica» disparan el rechazo
aunque no haya ninguna certificación de ventas. Si el lint se queja de una frase inocente,
reformularla es más barato que tocar el regex.

## Canciones destacadas por álbum (18-sep-2026)

Cada ficha de álbum marca entre 1 y 3 piezas clave con estrellas (1–5) y una frase. Es un
juicio **por álbum**, no por canción: son ~1300 decisiones, no las 13.534 pistas del atlas.
Las estrellas son de la canción, no del disco: en un álbum flojo la destacada puede llevar 2.

- `build_tareas_destacadas.py [--lote N] [--prefijo dest]` → `data/tareas_dest/<grupo>.json`
  con el tracklist verificado de cada álbum. Instrucciones en `data/tareas_dest/INSTRUCCIONES.md`.
- Redactores → `data/editorial_destacadas/<grupo>.json`:
  `{"albumes":[{"album_slug","destacadas":[{"medio","n","estrellas","nota"}]}]}`.
  Un álbum sin nada que rescatar lleva `"destacadas": []` con `"sin_destacadas": "motivo"`.
- `merge_destacadas.py [--check]` → `data/destacadas.json`, que consume la ficha de álbum
  (estrellas en la fila del tracklist + bloque «Las claves del disco»). Acumula por lote, así
  que se puede correr con el trabajo a medias. Lint: par (medio, n) inexistente, estrellas
  fuera de 1–5, más de 3 destacadas, nota vacía, de más de 220 caracteres o con datos duros.

**La clave es (medio, n), no n**: en los 94 álbumes de más de un disco los números de pista
se repiten entre medios. La primera versión de estos scripts aplanaba los medios y el disco 2
pisaba al disco 1 — el título publicado no era el de la canción elegida. Si se tocan estos
scripts, mantener el par completo.

### Lo que NO funcionó: extraer las destacadas del texto

`build_destacadas.py` cruza las citas «…» de las fichas con el tracklist. Se descartó como
fuente: marcar toda cita da el 71 % de las pistas y ponderar por sección deja fuera los discos
canónicos. Sirve como verificador (`--informe` lista las citas que no casan con ninguna pista,
que delatan títulos mal escritos en las historias).
