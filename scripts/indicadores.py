"""Los indicadores de LLACTA, calculados y fechados.

    python -I scripts/indicadores.py

Escribe `datos/indicadores.json` con el punto de hoy de la serie: cada
indicador con su valor, su radio, su fuente, su metodo y la version del metodo.

QUE CALCULA. Los tres indicadores de proximidad del observatorio: cuanta gente
de Riobamba vive a la distancia que fija la ordenanza de un area verde, de una
escuela y de un servicio de salud. No es «cuantos parques hay»: es a cuanta
gente llegan.

EL RADIO NO SE ESCRIBE AQUI. Se lee de `src/lib/norma.ts` del visor de
territorio, que es la transcripcion de la tabla 3 del articulo 178 del Codigo
Urbano con su cita. Si manana cambia la ordenanza y se corrige ese archivo, el
indicador cambia con ella sin que haya que tocar este script. Un radio escrito
a mano aqui seria un numero que nadie volveria a revisar.

Y EL RADIO DEPENDE DE LA TIPOLOGIA, no del uso. La tabla fija 400 m para el
parque barrial y 3.000 m para el parque zonal: son equipamientos distintos con
areas de influencia distintas, y medirlos juntos no significa nada. Por eso
cada indicador declara el par uso + tipologia, y los equipamientos de otra
tipologia no entran en esa medicion.

METODO. Reparto proporcional al area cubierta, el mismo de «Poblacion
alcanzada» de CHASKI:

    las coberturas se UNEN antes de medir
    fraccion cubierta de la manzana = area cubierta / area de la manzana
    alcanzados = poblacion de la manzana * fraccion

Las coberturas se unen porque se pisan casi siempre —el circulo de la escuela y
el del parque cubren la misma manzana—, y sumando los solapes una manzana
saldria cubierta al 180 %, con mas gente alcanzada de la que vive en ella.

Suponer a la gente repartida por igual dentro de la manzana es razonable a esa
escala, y cada vez menos segun la pieza crece. Queda dicho en la ficha del
indicador, que es donde se lee.

EL DENOMINADOR son los 200.179 habitantes que viven en manzana, no los 260.882
del canton: el 23 % restante es poblacion rural dispersa que no esta en ninguna
manzana del INEC, y meterla en el denominador diria que no tiene parque cuando
lo que pasa es que no se la esta midiendo. La cifra se lee del propio archivo.

LA CARTOGRAFIA DE MANZANAS no tiene precision metrica y el INEC lo advierte:
es para operativos de campo con fines estadisticos. Vale para repartir
poblacion; las superficies que salen de ella son orden de magnitud.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
VISOR = RAIZ.parent / "gadmr-visor-territorio"
DATOS = VISOR / "public" / "datos"
NORMA_TS = VISOR / "src" / "lib" / "norma.ts"

M = 32717          # UTM 17S, el CRS metrico de las capas municipales
SEGMENTOS = 64     # cuartos de circulo del buffer: 256 lados, 99,99 % del area

# La version del metodo. SE SUBE cuando el calculo cambia, para que la serie se
# corte a la vista en vez de comparar cifras que no son comparables.
VERSION_METODO = "1.0"

# Los tres indicadores. Cada uno declara el par uso + tipologia de la tabla 3;
# el radio lo pone la norma, no esta linea.
#
# OJO CON LAS TILDES. Los comentarios y el docstring de este archivo van en
# ASCII, como el resto de los scripts del visor. Lo que NO puede ir en ASCII es
# cualquier cadena que acabe publicada —el nombre del indicador, las fuentes,
# el metodo—, porque esas se leen en la portada: un rotulo que diga «area» en
# una pagina del municipio es un error. Por eso la consola imprime «?» donde
# hay tilde y el archivo de salida la lleva bien.
INDICADORES = [
    {
        "clave": "proximidad_area_verde",
        "nombre": "Gente con un área verde cerca",
        "tipo": "Recreativo y Deporte",
        "tipologia": "Barrial",
    },
    {
        "clave": "proximidad_escuela",
        "nombre": "Gente con una escuela cerca",
        "tipo": "Educacion",
        "tipologia": "Barrial",
    },
    {
        "clave": "proximidad_salud",
        "nombre": "Gente con un servicio de salud cerca",
        "tipo": "Salud",
        "tipologia": "Barrial",
    },
]


def log(m=""):
    print(str(m).encode("ascii", "replace").decode("ascii"), flush=True)


def sin_tildes(s: str) -> str:
    """Para casar «Educación» de la norma con «Educacion» de aqui."""
    pares = "áaéeíióoúuüuññ"
    for i in range(0, len(pares), 2):
        s = s.replace(pares[i], pares[i + 1]).replace(pares[i].upper(), pares[i + 1].upper())
    return s


def leer_norma() -> tuple[dict, str]:
    """La tabla 3 leida de norma.ts: {(uso sin tildes, tipologia): fila}."""
    if not NORMA_TS.exists():
        log(f"  ERROR: no esta {NORMA_TS}")
        log("  Sin la norma no hay radio, y el radio no se inventa.")
        sys.exit(1)
    texto = NORMA_TS.read_text(encoding="utf-8")

    cita = ""
    m = re.search(r"CITA_NORMA\s*=\s*\n?\s*'([^']+)'", texto)
    if m:
        cita = m.group(1)

    tabla: dict = {}
    # Cada uso abre con  'Educación': [  y dentro van sus niveles.
    for bloque in re.finditer(r"'([^']+)':\s*\[(.*?)\n  \]", texto, re.S):
        uso = bloque.group(1)
        for fila in re.finditer(
            r"\{\s*simbolo:\s*'([^']+)',\s*tipologia:\s*'([^']+)',\s*radio:\s*(\d+|null),"
            r".*?actividades:\s*'([^']*)'",
            bloque.group(2),
            re.S,
        ):
            simbolo, tipologia, radio, actividades = fila.groups()
            if radio == "null":
                continue  # la tabla pone «---»: sirve a toda la ciudad
            clave = (sin_tildes(uso), tipologia)
            # Si un uso trae dos filas con la misma tipologia —Seguridad tiene
            # la UPC a 400 m y los bomberos a 2.000— se queda la mas exigente,
            # que es la de proximidad.
            if clave not in tabla or int(radio) < tabla[clave]["radio"]:
                tabla[clave] = {
                    "simbolo": simbolo,
                    "tipologia": tipologia,
                    "radio": int(radio),
                    "actividades": actividades,
                    "uso": uso,
                }
    return tabla, cita


def main() -> None:
    import geopandas as gpd

    hoy = date.today().isoformat()
    log("=== LLACTA  ·  indicadores de proximidad ===")
    log(f"  fecha del punto: {hoy}  ·  metodo v{VERSION_METODO}")
    log()

    # ------------------------------------------------------------- la norma
    norma, cita = leer_norma()
    log(f"  norma leida de {NORMA_TS.name}: {len(norma)} niveles con radio")
    log(f"  {cita}")
    log()

    # ------------------------------------------------------------ las capas
    man = gpd.read_file(DATOS / "manzanas.geojson").to_crs(M)
    man["_area"] = man.geometry.area
    denominador = int(man["poblacion"].fillna(0).sum())
    log(f"  manzanas: {len(man):,}  ·  {denominador:,} habitantes en manzana")

    eq = gpd.read_file(DATOS / "equipamientos.geojson").to_crs(M)
    log(f"  equipamientos: {len(eq):,}")
    log()

    salida = []
    log(f"  {'indicador':<38} {'radio':>6} {'equip':>6} {'alcanzados':>12} {'%':>7}")
    log(f"  {'-'*38} {'-'*6} {'-'*6} {'-'*12} {'-'*7}")

    for ind in INDICADORES:
        nivel = norma.get((ind["tipo"], ind["tipologia"]))
        if not nivel:
            log(f"  {ind['nombre']}: la norma no fija radio para "
                f"{ind['tipo']} / {ind['tipologia']}. NO se publica.")
            continue
        radio = nivel["radio"]

        sel = eq[
            (eq["tipo"].map(sin_tildes) == ind["tipo"])
            & (eq["tipologia"] == ind["tipologia"])
        ]
        if sel.empty:
            log(f"  {ind['nombre']}: ningun equipamiento de esa tipologia. NO se publica.")
            continue

        def alcanzados(puntos) -> tuple[float, int, int]:
            """Poblacion alcanzada, manzanas enteras y manzanas a medias."""
            cob = puntos.geometry.buffer(radio, resolution=SEGMENTOS).union_all()
            cub = man.geometry.intersection(cob).area
            frac = (cub / man["_area"]).clip(upper=1.0).fillna(0.0)
            pob = man["poblacion"].fillna(0)
            return float((pob * frac).sum()), int((frac > 0.999).sum()), int(
                ((frac > 0.001) & (frac <= 0.999)).sum()
            )

        total, enteras, medias = alcanzados(sel)
        pct = total / denominador * 100

        # Sensibilidad: que pasa si lo que esta en mal estado no cuenta. Un
        # parque que no sirve no da cobertura a nadie, y la diferencia entre
        # las dos cifras es parte de lo que el observatorio tiene que ensenar.
        sirve = sel[sel["estado"].isin(["Bueno", "Regular"])]
        total_sirve, _, _ = alcanzados(sirve) if not sirve.empty else (0.0, 0, 0)

        log(f"  {ind['nombre']:<38} {radio:>5} m {len(sel):>6} {round(total):>12,} {pct:>6.1f} %")

        salida.append({
            "clave": ind["clave"],
            "nombre": ind["nombre"],
            "fecha": hoy,
            "ambito": "cantón Riobamba · población en manzana",
            "valor_pct": round(pct, 1),
            "alcanzados": round(total),
            "denominador": denominador,
            "radio_m": radio,
            "norma": {
                "simbolo": nivel["simbolo"],
                "uso": nivel["uso"],
                "tipologia": nivel["tipologia"],
                "actividades": nivel["actividades"],
                "cita": cita,
            },
            "equipamientos": int(len(sel)),
            "manzanas_cubiertas_enteras": enteras,
            "manzanas_cubiertas_a_medias": medias,
            "sin_contar_en_mal_estado": {
                "equipamientos": int(len(sirve)),
                "alcanzados": round(total_sirve),
                "valor_pct": round(total_sirve / denominador * 100, 1),
            },
            "metodo": (
                "Reparto proporcional al área cubierta. Las coberturas se unen "
                "antes de medir para no contar dos veces el solape. Supone la "
                "población repartida por igual dentro de cada manzana. Se mide "
                "en línea recta, no por la calle."
            ),
            "version_metodo": VERSION_METODO,
            "fuentes": [
                "Manzanas del INEC con la población del Censo 2022 repartida "
                "por edificios. La cartografía de manzanas no tiene precisión "
                "métrica: es de uso estadístico.",
                "Equipamientos del levantamiento municipal, con su tipo, "
                "tipología y estado.",
                cita,
            ],
        })

    # ----------------------------------------------------------- a disco
    destino = RAIZ / "datos"
    destino.mkdir(exist_ok=True)
    cuerpo = {
        "observatorio": "LLACTA",
        "generado": hoy,
        "version_metodo": VERSION_METODO,
        "indicadores": salida,
    }
    ruta = destino / "indicadores.json"
    ruta.write_text(
        json.dumps(cuerpo, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # El mismo contenido como script, que es lo que carga la portada.
    #
    # No es duplicar por gusto: un `fetch` de un archivo local lo bloquea el
    # navegador, asi que una pagina que lee el JSON no se puede abrir haciendo
    # doble clic —hace falta levantar un servidor para ver si quedo bien—. Con
    # un `<script>` la portada funciona desde el disco y desde GitHub Pages sin
    # cambiar nada. El JSON se queda porque es el registro: es lo que entra en
    # la serie y lo que se compara el ano que viene.
    (destino / "indicadores.js").write_text(
        "/* Generado por scripts/indicadores.py. No editar a mano. */\n"
        "window.LLACTA = " + json.dumps(cuerpo, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )

    log()
    for s in salida:
        d = s["sin_contar_en_mal_estado"]
        log(f"  {s['nombre']}")
        log(f"    {s['valor_pct']} %  ·  {s['alcanzados']:,} de {s['denominador']:,} hab")
        log(f"    {s['norma']['simbolo']} {s['norma']['tipologia']} a {s['radio_m']} m "
            f"· {s['equipamientos']} equipamientos")
        log(f"    manzanas: {s['manzanas_cubiertas_enteras']:,} enteras, "
            f"{s['manzanas_cubiertas_a_medias']:,} a medias")
        log(f"    sin los que estan en mal estado: {d['valor_pct']} % "
            f"({d['equipamientos']} equipamientos)")
        log()

    log(f"  {ruta}")
    log("listo")


if __name__ == "__main__":
    main()
