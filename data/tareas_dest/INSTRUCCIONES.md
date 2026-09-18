# Canciones destacadas por álbum — instrucciones para el redactor

Eres redactor del **Atlas del Prog**. Tu tarea no es puntuar todas las canciones: es
**elegir, de cada álbum, entre 1 y 3 piezas clave** y decir en una frase por qué lo son.

El resto del tracklist queda sin nota, igual que los charts sin fuente. Un disco no está
obligado a tener tres: si solo una pieza justifica el álbum, marcá una sola.

## Qué significa «destacada»

Las dos cosas que el atlas puede sostener:

- **Lo aclamado**: la pieza por la que el disco entró en la historia, la que citan quienes
  hablan de él, la que define su forma (la suite que ocupa una cara, el tema que fija el
  procedimiento del grupo).
- **Lo popular**: el corte que efectivamente se escuchó y se sigue escuchando, aunque la
  ficha lo trate con distancia.

Cuando ambas cosas coinciden, mejor. Cuando no, elegí y decilo en la nota: «el corte que
todo el mundo conoce, aunque el disco valga por otra cosa» es una nota legítima.

**No repartas premios por simetría**: en un disco flojo la destacada puede llevar 2 estrellas.
Las estrellas son de la canción, no del álbum.

## Salida

Un único archivo `data/editorial_destacadas/<id>.json`:

```json
{
 "albumes": [
  {
   "album_slug": "yes-close-to-the-edge",
   "destacadas": [
    {"medio": 1, "n": 1, "estrellas": 5, "nota": "Dieciocho minutos que justifican su duración: el argumento central del disco y del género."},
    {"medio": 1, "n": 3, "estrellas": 4, "nota": "El riff que prueba que el grupo podía ser físico sin renunciar a la complejidad."}
   ]
  }
 ]
}
```

- `medio` y `n` identifican la pista **tal como vienen en el tracklist del manifiesto**.
  En los 94 álbumes de más de un disco los números se repiten entre discos, así que
  `medio` es obligatorio para distinguir la pista 1 del disco 1 de la pista 1 del disco 2.
  El merge rechaza cualquier par (medio, n) que no exista: no inventes pistas ni uses el
  número de otra edición. En álbumes de un solo disco, `medio` es siempre 1.
- `estrellas`: entero de 1 a 5, criterio de la canción.
- `nota`: **una sola frase**, máximo 220 caracteres, con criterio y sin relleno.
- Cada álbum del manifiesto debe aparecer exactamente una vez.

## Método

1. Leé tu manifiesto `data/tareas_dest/<id>.json`: trae el tracklist verificado de cada
   álbum con los números de pista, más año, escena y estrellas del álbum.
2. **Abrí la ficha de cada álbum** (`content/albumes/<slug>.md`): la entradilla y la historia
   larga ya discuten el disco. Tu elección tiene que ser coherente con lo que ahí se dice —
   si la historia argumenta que la cara B es el corazón del disco, no destaques el single.
3. Escribí el JSON con Python (`json.dump`, `ensure_ascii=False`, `indent=1`), guardando cada
   tantos álbumes para no perder trabajo.
4. Verificá con `python3 pipeline/merge_destacadas.py --check`.

## Reglas duras (el merge lintea y descarta el álbum)

- **Ningún dato de chart, ventas ni certificaciones** en la nota (ni «fue número uno», ni
  «vendió millones», ni «disco de oro»).
- **Ninguna fecha completa** (día y mes).
- Nada de adjetivos huecos: «icónico», «legendario», «mítico», «inolvidable».
- Sin citas textuales inventadas ni atribuciones que la ficha no sostenga.
- Ojo con el verbo «certifica»: el lint lo confunde con una certificación de ventas.

## Discos sin nada que destacar

Si la ficha dice explícitamente que no hay pieza que rescatar —pasa con la música de
librería y con algunas reediciones tardías—, no fuerces una elección: escribí

```json
{"album_slug": "…", "destacadas": [], "sin_destacadas": "librería funcional: la ficha no rescata ninguna pieza"}
```

Es preferible a inventar un destaque que la ficha contradice.

## Suites y pistas largas

Si una pista del tracklist contiene varios movimientos («Close to the Edge: The Solid Time
of Change / Total Mass Retain / …»), destacás la pista entera con su número; podés nombrar
el movimiento en la nota.
