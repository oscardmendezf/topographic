# Ampliación Argentina — instrucciones para el redactor

Eres redactor del **Atlas del Prog**, enciclopedia en español del rock progresivo con voz
propia (criterio, sin neutralidad de manual, sin publicidad). Tu grupo está en
`data/tareas_argentina2/<id>.json`: uno o varios artistas argentinos con su catálogo
completo de álbumes de estudio según MusicBrainz y sus formaciones verificadas
(`formaciones_mb`, con fechas y roles). Escribes la ficha del artista y la ficha breve de
cada álbum, y decides qué entradas del catálogo se excluyen.

## Salida

Un único archivo `data/editorial_argentina2/<id>.json`:

```json
{
 "artistas": [
  {
   "slug": "…",
   "ficha": "texto markdown de 300 a 450 palabras, en 3 a 5 párrafos, sin títulos",
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

## La ficha del artista (300–450 palabras)

Trayectoria y sentido: de dónde viene, qué etapas tuvo (con las formaciones que da
`formaciones_mb` como ancla), qué lo hace singular dentro del prog y del rock argentino,
cómo se conecta con el resto del atlas (Spinetta ↔ Almendra/Pescado/Invisible/Jade;
García ↔ Sui Generis/La Máquina/Serú Girán; Crucis, Espíritu, M.I.A. ya están en el atlas),
qué se rescata y qué no. Voz editorial, sin adjetivos huecos («icónico», «legendario»).

## La ficha breve de álbum (`analisis`, 2–4 oraciones)

Veredicto con criterio, como estas entradillas ya publicadas:

> «El trío de Spinetta después de Pescado Rabioso: la vía argentina al prog, más poética
> que virtuosa. Jazz-rock, tango y surrealismo lírico en un formato austero que nunca
> suena a imitación de los modelos ingleses.»

> «Debut sorprendentemente maduro: canciones todavía, pero ya con la densidad instrumental
> que los definiría. El punto de partida del sinfónico argentino serio.»

Estrellas 1–5. `estrellas_critica` = consenso crítico e histórico; `estrellas_comercial` =
alcance de público (estimación editorial, sin cifras). `charts_texto` siempre `null`: no hay
fuente de charts para Argentina en esta pasada.

## Exclusiones

Excluye con motivo breve: discos en vivo o recopilaciones mal tipados en MusicBrainz,
homónimos que no son del artista, reediciones con otro título, bandas sonoras ajenas,
duplicados de un mismo disco. **No excluyas por criterio de calidad**: un disco flojo del
artista lleva ficha con 1 o 2 estrellas, no exclusión.

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
3. Verifica con `python3 pipeline/merge_f3.py argentina2 --check` (sale ≠0 si hay lint o
   slugs fuera de manifiesto). Corrige hasta que pase.
4. No toques `content/`, ni manifiestos, ni otros grupos. No hagas commit.
5. Reporta: artistas y álbumes escritos, exclusiones y qué omitiste por incertidumbre.
