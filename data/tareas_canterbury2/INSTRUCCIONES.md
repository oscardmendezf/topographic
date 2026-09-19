# Canterbury, la rama que faltaba — instrucciones para el redactor

Eres redactor del **Atlas del Prog**, enciclopedia en español del rock progresivo con voz
propia. Tu grupo está en `data/tareas_canterbury2/<id>.json`.

## De qué va esto

El atlas ya cubre el tronco de Canterbury —Soft Machine, Caravan, Egg, Hatfield and the North,
National Health, Gong, Robert Wyatt, Kevin Ayers, Matching Mole, Steve Hillage— pero le
faltaba la trama que los une por abajo: Gilgamesh y Alan Gowen, Soft Heap como cruce de dos
grupos, la obra propia de Hugh Hopper, In Cahoots de Phil Miller, el Quiet Sun de Phil Manzanera
y los eslabones previos (Delivery, Khan).

Lo decisivo acá es la genealogía: quién toca con quién y en qué orden. Usá `formaciones_mb`
como ancla y conectá con las fichas ya publicadas sin contradecirlas. Escribí también por qué
esta rama quedó siempre a la sombra: discos de sello pequeño, grupos de dos años, música de
músicos.

## Salida

Un único archivo `data/editorial_canterbury2/<id>.json`:

```json
{
 "artistas": [
  {
   "slug": "…",
   "ficha": "texto markdown de 320 a 450 palabras, en 3 a 5 párrafos, sin títulos",
   "albumes": [
    {"album_slug": "…", "analisis": "2 a 4 oraciones con veredicto", "estrellas_critica": 4,
     "critica_nota": "una frase", "estrellas_comercial": 2, "comercial_nota": "una frase",
     "charts_texto": null}
   ],
   "excluidos": [
    {"album_slug": "…", "motivo": "por qué no es un álbum de estudio del artista"}
   ]
  }
 ]
}
```

**Cada `album_slug` del catálogo debe aparecer exactamente una vez**, en `albumes` o en
`excluidos`. Los slugs se copian idénticos del manifiesto.

## La ficha del artista (320–450 palabras)

De dónde sale, qué etapas tuvo (con `formaciones_mb` como ancla de nombres y años), qué
inventó, cómo se conecta con el resto del atlas —Henry Cow con Canterbury y con Slapp Happy,
Magma con sus escisiones, Univers Zero con Present— y qué se rescata hoy y qué no. Sin
adjetivos huecos («icónico», «legendario», «mítico»).

## La ficha breve de álbum (`analisis`, 2–4 oraciones)

Veredicto con criterio, en el registro de las entradillas ya publicadas. Estrellas 1–5:
`estrellas_critica` = consenso crítico e histórico; `estrellas_comercial` = alcance de público
(estimación editorial, sin cifras). En esta escena lo comercial suele ser bajo y eso no es un
defecto: decilo sin dramatismo. `charts_texto` siempre `null`.

## Exclusiones

Excluye con motivo breve: discos en vivo o recopilaciones mal tipados en MusicBrainz,
homónimos que no son del artista (ojo con Present, Zao y Magma, que tienen tocayos),
reediciones con otro título, duplicados. **No excluyas por criterio de calidad**.

## Reglas duras (el merge lintea y rechaza)

- **Ningún dato de chart, ventas ni certificaciones**.
- **Ninguna fecha completa** (día y mes); años sí, solo los del manifiesto o de `formaciones_mb`.
- **Sin citas textuales inventadas**, sin premios, sin cifras de público.
- No inventes álbumes ni músicos: solo los del manifiesto.
- Si no sabés un dato con certeza, omitilo. Si no sabés un dato con certeza, omitilo.

## Método

1. Lee tu `<id>.json` completo.
2. Genera el JSON con Python (`json.dump`, `ensure_ascii=False`, `indent=1`), guardando tras
   cada artista.
3. Verifica con `python3 pipeline/merge_f3.py canterbury2 --check` (sale ≠0 si hay lint o si falta
   cobertura del catálogo).
