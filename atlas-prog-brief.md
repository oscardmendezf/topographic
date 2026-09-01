# Atlas del Prog — Brief de proyecto

> Documento de arranque para el repositorio. Escrito el 31-ago-2026 tras el prototipo
> editorial `mapa-del-prog.html` (incluirlo en el repo como referencia de tono y contenido).

## Visión
Una enciclopedia navegable del rock progresivo y los álbumes conceptuales, en **español**,
con forma de **grafo genealógico clickeable**: artistas, personas, discos, sellos y estudios
como nodos; membresías, producciones, arreglos e influencias como aristas. El usuario debe
poder perderse horas siguiendo ramas.

## Qué ya existe (no competir en su terreno)
- **Discogs / MusicBrainz**: datos duros exhaustivos (créditos, formaciones, ediciones). Imbatibles en completitud.
- **BandToBand.com**: grafo clickeable de bandas conectadas por miembros. Sin análisis, sin discografías profundas.
- **ProgArchives / RateYourMusic**: discografías del género con reseñas de comunidad.
- **Pete Frame's Rock Family Trees**: la genealogía como arte, en papel.

## Diferencial (el terreno propio)
1. **Curaduría con voz**: análisis breve y con criterio por disco/artista/conexión (el prototipo HTML es la muestra de tono).
2. **Grafo interpretativo**: no solo "quién tocó con quién" sino productores, arreglistas, estudios y sellos como nodos de primera clase (Hitchcock, Bedford, Offord, Virgin, Manticore...).
3. **Español**: todo el ecosistema existente está en inglés.
4. **Verificabilidad delegada**: cada nodo enlaza a su ID de MusicBrainz + Discogs + Wikipedia. No replicamos datos: los citamos.

## Reglas editoriales (aprendidas empíricamente en el prototipo)
- **Ningún dato de chart/fecha escrito de memoria.** Todo dato duro viene de la API o se marca `s.d.`. (La memoria del modelo demostró inventar entradas de chart inexistentes y trasponer posiciones.)
- **Influencias: solo autodeclaradas y con fuente** (entrevista, liner notes). Sin fuente, no hay arista de influencia.
- Diferenciar tipos de ficha: **individual** (discos con peso narrativo) vs **bloque de etapa** (resto del catálogo, nombrado título por título).
- Datos inciertos se declaran, nunca se maquillan.

## Modelo de datos (propuesta inicial)
Nodos: `artist`, `person`, `album`, `label`, `studio`, `scene`.
Aristas tipadas y con rango temporal: `member_of`, `produced`, `engineered`, `arranged`,
`guested_on`, `designed_artwork`, `signed_to`, `recorded_at`, `influenced(source_url)`.
Cada nodo: `mbid` (MusicBrainz ID), `discogs_id`, `wikipedia_url`, `analisis_md` (nuestra capa).

## Stack sugerido (discutir en la primera sesión de Code)
- **Datos**: scripts (Python o TS) contra la API de MusicBrainz → SQLite o JSON versionado en el repo.
- **Sitio**: generador estático (Astro) — barato de hospedar, indexable, rápido.
- **Grafo**: Cytoscape.js (o D3 si se quiere control fino). Vistas: grafo global filtrable + línea de tiempo + ficha por nodo.
- **Despliegue**: GitHub Pages / Cloudflare Pages.

## MVP (Fase 1 — cerrada, no negociable en alcance)
Exactamente el universo del prototipo: **26 artistas de la era clásica 1966-1980** + la red
de ~20 conexiones ya documentada. Nada más hasta que esto funcione end-to-end:
1. Pipeline: bajar de MusicBrainz los 26 artistas con miembros, discos y relaciones.
2. Capa editorial: migrar los análisis del HTML a markdown por nodo.
3. Grafo navegable + ficha por nodo con links de verificación.
4. Deploy.

## Fases posteriores (en orden, una por vez)
F2: continuación 1981-presente. F3: Canterbury profundo, Italia, Alemania (contenido ya
redactado en el prototipo). F4: herederos (Marillion, Asia, neoprog). F5: influencias
sonoras/instrumentos (Mellotron, VCS3...) como nodos, si el modelo aguanta.

## Riesgo nº 1
El alcance. Cada sesión de trabajo empieza declarando qué fase toca y termina sin abrir la
siguiente. El proyecto muere por expansión prematura, no por falta de ideas.

## Assets existentes
- `mapa-del-prog.html` (122 KB): 282 fichas, 26 artistas, red, herederos, fronteras.
  Estado de verificación de datos documentado en su encabezado y pie.
