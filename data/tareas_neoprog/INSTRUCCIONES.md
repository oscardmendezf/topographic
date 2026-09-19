# Escena «Neoprog» — instrucciones para el redactor

Eres redactor del **Atlas del Prog**, enciclopedia en español del rock progresivo con voz
propia. Tu grupo está en `data/tareas_neoprog/<id>.json`.

## De qué va esta escena

El neoprog es la generación que recoge el género cuando ya estaba oficialmente muerto: a
principios de los ochenta, con el punk encima y el prog convertido en insulto, un puñado de
bandas británicas decide que la forma larga, los teclados en capas y las letras narrativas
todavía servían. Marillion es el caso central y el más incómodo: acusada de imitar a Genesis
con Fish haciendo de Gabriel, terminó escribiendo su propio repertorio y sobreviviendo al
cambio de cantante, que es más de lo que lograron sus modelos.

Escribí sin las dos comodidades habituales: ni el desprecio del crítico que lo despacha como
copia, ni la defensa cerrada del aficionado. Preguntas útiles: qué añadieron al vocabulario
que heredaron, qué se limitaron a repetir, y por qué la etiqueta «neo» sigue funcionando como
condena. Marcá también la ruptura técnica —producción de los ochenta, batería electrónica,
teclados digitales— frente al sonido de la era clásica que el atlas ya cubre.

## Salida

Un único archivo `data/editorial_neoprog/<id>.json`:

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
3. Verifica con `python3 pipeline/merge_f3.py neoprog --check` (sale ≠0 si hay lint o si falta
   cobertura del catálogo).
