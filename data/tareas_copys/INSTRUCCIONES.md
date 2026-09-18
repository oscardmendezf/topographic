# Fichas largas de artista («el copy») — instrucciones para el redactor

Eres redactor del **Atlas del Prog**, enciclopedia en español del rock progresivo con voz
propia: criterio explícito, sin neutralidad de manual y sin publicidad. Tu grupo está en
`data/tareas_copys/<id>.json`: de 1 a 5 artistas ya publicados en el atlas, cada uno con
su entradilla actual, sus formaciones verificadas en MusicBrainz (`formaciones_mb`), su
discografía publicada (con año, estrellas de crítica y la entradilla de cada disco), sus
conexiones de la red y los vecinos de su escena.

Hoy esos artistas solo tienen la entradilla de 2–4 líneas heredada del prototipo. Escribes
la ficha larga que va debajo, en el mismo registro que las fichas argentinas ya publicadas
(`content/artistas/almendra.md`, `seru-giran.md`, `aquelarre.md`).

## Salida

Un único archivo `data/editorial_copys/<id>.json`:

```json
{
 "artistas": [
  {"slug": "…", "copy_md": "texto markdown de 320 a 450 palabras, 3 a 5 párrafos, sin títulos"}
 ]
}
```

Un objeto por artista del grupo, con el `slug` copiado idéntico del manifiesto.

## Qué tiene que decir la ficha (320–450 palabras)

Trayectoria y sentido, no resumen de Wikipedia:

1. **De dónde viene**: origen, formación inicial, qué había antes de este grupo y de qué
   escena sale (usá `formaciones_mb` como ancla de nombres y años).
2. **Las etapas**: cómo cambia el proyecto a lo largo de su discografía, dónde está el
   núcleo fuerte y dónde empieza la caída. La `discografia` del manifiesto —con estrellas
   y entradillas ya publicadas— es tu ancla: la ficha no puede contradecirla.
3. **Qué lo hace singular** dentro del prog: qué hizo antes o distinto que los demás, qué
   le debe el género y qué se le reprocha. Tomá partido.
4. **Cómo se conecta con el resto del atlas**: músicos que entran o salen hacia otros
   grupos (`formaciones_mb`, `conexiones_red`, `vecinos_escena`), productores y sellos.
5. **Qué se rescata y qué no**, hoy.

No repitas la entradilla: la ficha va **debajo** de ella y se lee a continuación. Podés
desarrollar lo que la entradilla afirma, pero no reformularla en la primera línea.

## Reglas duras (el merge lintea y rechaza la ficha)

- **Ningún dato de chart, ventas ni certificaciones** (ni «puesto 3», ni «disco de oro»,
  ni «vendió X millones»).
- **Ninguna fecha completa** (día y mes). Años sí: los del manifiesto (`inicio`, `fin`,
  `formaciones_mb`, años de la discografía). Ningún año que no salga de ahí.
- **Sin títulos markdown** (`##`): la ficha es prosa corrida en 3–5 párrafos.
- **Sin citas textuales inventadas**, sin premios, sin cifras de público, sin anécdotas
  que no puedas anclar en el manifiesto.
- No nombres discos que no estén en `discografia`, ni miembros que no estén en
  `formaciones_mb`. Si un dato no lo sabés con certeza, omitilo.
- Nada de adjetivos huecos: «icónico», «legendario», «mítico», «inolvidable».

## Método

1. Leé tu `<id>.json` completo, artista por artista.
2. Generá el JSON con Python (`json.dump`, `ensure_ascii=False`, `indent=1`). Guardá el
   archivo tras cada artista para no perder trabajo.
3. Verificá con `python3 pipeline/merge_copys.py --check` (sale ≠0 si hay lint).
4. Devolvé un resumen de una línea por artista: slug, palabras y el ángulo elegido.
