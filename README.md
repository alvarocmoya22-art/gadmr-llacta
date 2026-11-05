# LLACTA · Observatorio Urbano de Riobamba

> **Prototipo.** Las cifras de aquí se publican para revisarlas, no para sacar
> una de un expediente sin mirarla.

*Llakta*, en kichwa, nombra a la vez al pueblo y a la gente del pueblo. Este
observatorio mide el territorio por la gente que vive en él.

El encargo completo está en [`PROMPT.md`](PROMPT.md): las cuatro ventanas, los
ocho indicadores, el esquema de la base de datos y las reglas de trabajo.

## Las cuatro ventanas

La interfaz es `index.html`. Cada ventana dice qué hace y si está lista; la que
no existe se ve que no existe, en vez de ser un enlace que no lleva a nada.

| Ventana | Qué hace | Estado |
|---|---|---|
| **Visor** | Ver el territorio | Publicado, fuera de este repositorio |
| **CHASKI** | Analizar y decidir | Publicado, fuera de este repositorio |
| **Mapoteca** | Descargar las capas con su ficha | `mapoteca.html` · 15 capas, 21,6 MB |
| **Levantamiento** | Verificar lo que se recoge en campo | **Todavía no.** Necesita la base de datos |

## Lo que hay hoy

**Los tres indicadores de proximidad**, calculados y fechados. El primer punto
de la serie.

| Indicador | Norma | Radio | Alcanzados | % |
|---|---|---|---|---|
| Gente con un área verde cerca | ED1 Barrial | 400 m | 98.498 | 49,2 % |
| Gente con una escuela cerca | EE1 Barrial | 400 m | 118.518 | 59,2 % |
| Gente con un servicio de salud cerca | ES1 Barrial | 800 m | 45.789 | 22,9 % |

Sobre 200.179 habitantes que viven en alguna manzana del INEC, el 76,7 % del
cantón. Dato del 4 de noviembre de 2026, método v1.0.

## Cómo se vuelve a calcular

```
python -I scripts/indicadores.py
python -I scripts/comprobar_indicadores.py
python -I scripts/mapoteca.py
```

El primero escribe `datos/indicadores.json` —el registro que entra en la serie—
y `datos/indicadores.js`, que es lo que carga la portada. El segundo vuelve a
sacar cada cifra por otros dos caminos geométricos. El tercero rehace el
catálogo de la Mapoteca abriendo las capas publicadas.

Para ver la interfaz basta abrir `index.html`; no hace falta servidor, y por eso
las páginas leen el `.js` y no el `.json`.

## Lo que la Mapoteca deja a la vista

El catálogo no está solo para descargar. Al construirlo contra los archivos
reales salieron dos cosas que no se veían:

- **Dos capas publicadas no entran en CHASKI**: `parroquias.geojson` (las 5
  urbanas) y `red_vial.geojson`. El visor las sirve y el analizador no las
  ofrece, así que hoy nadie las puede cruzar con nada sin bajárselas a mano.
- **Tres capas tienen la licencia sin confirmar**: `calles.json`, `red.json` y
  `red_vial.geojson`, marcadas como ODbL por deducción. En un catálogo público
  eso hay que confirmarlo, no suponerlo.

## El radio no se escribe en ninguna parte de este proyecto

Se lee de `src/lib/norma.ts` del visor de territorio, que es la transcripción de
la **tabla 3 del artículo 178 del Código Urbano de Riobamba** (Registro Oficial
E.E. 885, 23 de mayo de 2023) con su cita. Si la ordenanza cambia y se corrige
ese archivo, los indicadores la siguen sin tocar nada de aquí.

Y el radio **depende de la tipología, no del uso**: el parque barrial tiene
400 m de área de influencia y el zonal 3.000. Son equipamientos distintos y
medirlos juntos no significaría nada.

## Lo que estas cifras no saben

- **Se mide en línea recta, no por la calle**, así que son optimistas. Y
  Riobamba está a 2.750 m y sube.
- **Suponen la población repartida por igual dentro de cada manzana.**
  Razonable a esa escala, cada vez menos según la pieza crece.
- **La cartografía de manzanas del INEC no tiene precisión métrica** —el propio
  INEC lo advierte—: vale para repartir población, no para medir superficies.
- **No miden el área rural dispersa**, que es el 23 % del cantón que no vive en
  ninguna manzana.
- **Un equipamiento en mal estado sigue contando** en la cifra principal. La
  columna «solo los que sirven» lo deja fuera, y la diferencia entre las dos es
  cuánta gente tiene cerca algo que no le sirve.

## Comprobación

Dos implementaciones del reparto proporcional que no comparten una línea
—intersección contra la unión de coberturas, y `overlay` cruzando las dos
capas— dan **la misma cifra, 0,000 % de diferencia** en los tres indicadores. El
método tosco del centroide, que cuenta la manzana entera o nada, queda entre
0,4 % y 0,9 % por debajo, que es lo que tiene que pasar.

**Falta la comprobación de verdad:** volver a sacar las tres cifras con CHASKI,
que implementa el mismo método en otro lenguaje y con otro código. Lo de aquí
comprueba la implementación, no el método.

## Estructura

```
PROMPT.md                        El encargo completo
index.html                       La interfaz: las cuatro ventanas
mapoteca.html                    El catálogo de capas
estilo.css                       El sistema de diseño del GADM
comun.js                         Formato es-EC y escape, compartidos
iconos.js                        Los iconos, dibujados aquí
mapa.js                          Los dos mapas, la tabla y los paneles
scripts/escalas.py               Indicadores por parroquia y mapa de manzanas
scripts/red_cercania.py          La red vial por cercanía
datos/indicadores.json           El registro: lo que entra en la serie
datos/indicadores.js             Lo mismo, como script, para las páginas
datos/capas.json                 El catálogo de la Mapoteca
datos/capas.js                   Lo mismo, como script
scripts/indicadores.py           El cálculo de los indicadores
scripts/comprobar_indicadores.py La comprobación
scripts/mapoteca.py              El catálogo, leído de las capas publicadas
```

## Lo siguiente

1. Comprobar las tres cifras con CHASKI, que es la comprobación de verdad.
2. Revisar la clasificación de Salud: seis subcentros barriales para todo el
   cantón no cuadra, y de ahí sale el 22,9 %.
3. Campos calculados y comparadores numéricos en CHASKI → desbloquean el
   indicador 5, la desigualdad del reparto.
4. El esquema de la base, con los ámbitos y el método versionados.
5. La ventana de Levantamiento sobre ese esquema.
