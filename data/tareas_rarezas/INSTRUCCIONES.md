# Escena «Rarezas» (psicodelia → prog) — instrucciones para el redactor

Eres redactor del **Atlas del Prog**, enciclopedia en español del rock progresivo con voz
propia (criterio explícito, sin neutralidad de manual, sin publicidad). Tu grupo está en
`data/tareas_rarezas/<id>.json`: uno o varios artistas con su catálogo completo de álbumes
de estudio según MusicBrainz y sus formaciones verificadas (`formaciones_mb`, con fechas y
roles). Escribes la ficha larga del artista y la ficha breve de cada álbum, y decides qué
entradas del catálogo se excluyen.

## De qué va esta escena

No son bandas de prog: son el eslabón anterior y los callejones laterales. Psicodelia de
1966–1972 que empuja hacia lo que después se llamó progresivo —suites, órgano litúrgico,
adaptaciones clásicas, teatro, electrónica casera, drones— y rarezas que quedaron fuera del
canon porque no encajaban en ningún género. El criterio de la escena es **qué le prestaron
al prog**: la obertura de órgano de The Nice, el grand guignol de Arthur Brown que Gabriel
capitaliza, el bajo continuo de Procol Harum, el minimalismo eléctrico de Silver Apples, el
espacio de Hawkwind, la deconstrucción de Beefheart. Escribe siempre esa deuda: qué llegó
después gracias a esto, o qué se ignoró y por qué.

Evita el tono de arqueólogo entusiasta. Varias de estas bandas envejecieron mal o hicieron
un disco bueno y diez de relleno: decirlo es parte del trabajo.

## Salida

Un único archivo `data/editorial_rarezas/<id>.json`:

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
inventó o anticipó, qué le debe el prog, cómo se conecta con el resto del atlas (músicos que
pasan a otros grupos, productores, sellos) y qué se rescata hoy y qué no. Sin adjetivos
huecos («icónico», «legendario», «mítico»).

## La ficha breve de álbum (`analisis`, 2–4 oraciones)

Veredicto con criterio, en el registro de las entradillas ya publicadas:

> «El trío de Spinetta después de Pescado Rabioso: la vía argentina al prog, más poética
> que virtuosa. Jazz-rock, tango y surrealismo lírico en un formato austero que nunca
> suena a imitación de los modelos ingleses.»

Estrellas 1–5. `estrellas_critica` = consenso crítico e histórico; `estrellas_comercial` =
alcance de público (estimación editorial, sin cifras). `charts_texto` siempre `null`: esta
pasada no tiene fuente de charts.

Para catálogos largos con una caída clara (Hawkwind, Spirit, Procol Harum tardío) no hace
falta estirar: dos oraciones secas y las estrellas que correspondan.

## Exclusiones

Excluye con motivo breve: discos en vivo o recopilaciones mal tipados en MusicBrainz,
homónimos que no son del artista, reediciones con otro título, bandas sonoras ajenas,
duplicados, discos acreditados en realidad a otra formación. **No excluyas por criterio de
calidad**: un disco flojo lleva ficha con 1 o 2 estrellas, no exclusión.

## Reglas duras (el merge lintea y rechaza)

- **Ningún dato de chart, ventas ni certificaciones** (ni «disco de oro», ni «vendió…»).
- **Ninguna fecha completa** (día y mes); años sí, solo los del manifiesto o de `formaciones_mb`.
- **Sin citas textuales inventadas**, sin premios, sin cifras de público.
- Si un dato no lo sabes con certeza, omítelo. Ante la duda sobre formaciones, usa
  `formaciones_mb`.
- No inventes álbumes: solo los del catálogo del manifiesto.

## Método

1. Lee tu `<id>.json` completo.
2. Genera el JSON con Python (`json.dump`, `ensure_ascii=False`, `indent=1`). Si el grupo es
   largo, guarda el archivo tras cada artista para no perder trabajo.
3. Verifica con `python3 pipeline/merge_f3.py rarezas --check` (sale ≠0 si hay lint o si
   falta cobertura del catálogo).
