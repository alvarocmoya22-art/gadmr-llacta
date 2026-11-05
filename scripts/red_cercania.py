"""La red vial de Riobamba dibujada por lo cerca que queda cada servicio.

    python -I scripts/red_cercania.py

Escribe `datos/red.js`: los 17.636 tramos de la red vial como polilineas SVG,
cada uno con la distancia en metros al equipamiento mas cercano de cada uno de
los tres indicadores.

POR QUE LA RED Y NO LAS MANZANAS. El mapa de manzanas contesta «a cuanta gente
alcanza», que es el indicador. Este contesta otra cosa: «como esta construida
la ciudad respecto a sus servicios». Dibujar la calle en vez del bloque ensena
la forma del tejido —el damero del centro, los caminos que salen al campo— y
deja ver el gradiente continuo que un bloque pintado de un solo color aplasta.

ES UNA SEGUNDA LECTURA, NO EL INDICADOR. Aqui no hay poblacion: una calle larga
y vacia pesa lo mismo que una del centro. Sirve para entender la forma, no para
sacar una cifra, y la pagina lo dice donde se lee.

LA DISTANCIA ES EN LINEA RECTA desde el punto medio de cada tramo. Por la calle
siempre es mayor, asi que este dibujo tambien es optimista. Medirla por la red
con un Dijkstra es lo siguiente, y el visor ya lo tiene resuelto para isocronas.

DE DONDE SALE LA RED. De `red.json` del visor, que es el grafo que usa para sus
isocronas: nodos, aristas, metros ya medidos y el trazado de cada una. Es
OpenStreetMap, asi que es ODbL y va citado.
"""
import json
import sys
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
DATOS = RAIZ.parent / "gadmr-visor-territorio" / "public" / "datos"

M = 32717
LADO = 2000
SIMPLIFICA = 8      # metros
TOPE = 3000         # mas alla de esto da igual: esta lejos y punto


def log(m=""):
    print(str(m).encode("ascii", "replace").decode("ascii"), flush=True)


def sin_tildes(s: str) -> str:
    pares = "áaéeíióoúuüuññ"
    for i in range(0, len(pares), 2):
        s = s.replace(pares[i], pares[i + 1]).replace(pares[i].upper(), pares[i + 1].upper())
    return s


def main() -> None:
    import geopandas as gpd
    import numpy as np
    from shapely import STRtree
    from shapely.geometry import LineString

    ficha = RAIZ / "datos" / "indicadores.json"
    if not ficha.exists():
        log("corre antes scripts/indicadores.py")
        sys.exit(1)
    inds = json.loads(ficha.read_text(encoding="utf-8"))["indicadores"]

    hoy = date.today().isoformat()
    log("=== LLACTA  ·  la red vial por cercania ===")

    crudo = json.loads((DATOS / "red.json").read_text(encoding="utf-8"))
    trazados = [a[3] for a in crudo["aristas"] if a[3] and len(a[3]) >= 2]
    log(f"  tramos: {len(trazados):,}  ·  fuente: {crudo['fuente']}")

    red = gpd.GeoSeries(
        [LineString(t) for t in trazados], crs=4326
    ).to_crs(M).simplify(SIMPLIFICA, preserve_topology=False)
    log(f"  km: {red.length.sum()/1000:,.1f}")

    eq = gpd.read_file(DATOS / "equipamientos.geojson").to_crs(M)

    # El punto medio de cada tramo, que es desde donde se mide.
    medios = red.interpolate(0.5, normalized=True)
    mx = np.array([p.x for p in medios])
    my = np.array([p.y for p in medios])

    distancias = []
    for ind in inds:
        n = ind["norma"]
        sel = eq[
            (eq["tipo"].map(sin_tildes) == sin_tildes(n["uso"]))
            & (eq["tipologia"] == n["tipologia"])
        ]
        arbol = STRtree(list(sel.geometry))
        _, d = arbol.query_nearest(list(medios), return_distance=True, all_matches=False)
        d = np.minimum(np.round(d / 10) * 10, TOPE).astype(int)
        distancias.append(d)
        dentro = int((d <= ind["radio_m"]).sum())
        log(f"  {ind['clave']:<28} {len(sel):>3} equip  ·  "
            f"{dentro:>6,} tramos dentro de los {ind['radio_m']} m  "
            f"({dentro/len(red)*100:4.1f} %)  ·  mediana {int(np.median(d)):,} m")

    # ------------------------------------------------------------ el dibujo
    #
    # LA MISMA TRANSFORMACION QUE EL MAPA DE MANZANAS, anclada al canton. Los
    # dos dibujos tienen que quedar superpuestos: comparten los limites de
    # parroquia y sus rotulos, y cambiar de vista no puede mover el mapa.
    par = gpd.read_file(DATOS / "parroquias_canton.geojson").to_crs(M)
    caja = par.total_bounds
    x0, y0 = caja[0], caja[3]
    escala = LADO / max(caja[2] - caja[0], caja[3] - caja[1])
    urb = par[par["tipo"] == "urbana"]
    cajaU = urb.total_bounds if len(urb) else caja

    lineas = []
    for i, geom in enumerate(red):
        if geom.is_empty:
            continue
        partes = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
        pts = []
        for parte in partes:
            prev = None
            for x, y in parte.coords:
                px = round((x - x0) * escala)
                py = round((y0 - y) * escala)
                if (px, py) != prev:
                    pts.append(f"{px},{py}")
                    prev = (px, py)
        if len(pts) >= 2:
            lineas.append({
                "p": " ".join(pts),
                "d": [int(dd[i]) for dd in distancias],
            })

    def a_svg(b):
        return [round((b[0] - x0) * escala), round((y0 - b[3]) * escala),
                round((b[2] - b[0]) * escala), round((b[3] - b[1]) * escala)]

    cuerpo = {
        "generado": hoy,
        "fuente": crudo["fuente"],
        "tope_m": TOPE,
        "indicadores": [
            {"clave": i["clave"], "nombre": i["nombre"], "radio_m": i["radio_m"]}
            for i in inds
        ],
        "m_por_unidad": round(1 / escala, 4),
        "velocidad_m_min": 75,   # 4,5 km/h, la misma que el visor usa para sus isocronas
        "viewBox": {"canton": a_svg(caja), "ciudad": a_svg(cajaU)},
        "tramos": lineas,
    }

    destino = RAIZ / "datos"
    destino.mkdir(exist_ok=True)
    ruta = destino / "red.js"
    ruta.write_text(
        "/* Generado por scripts/red_cercania.py. No editar a mano. */\n"
        "window.LLACTA_RED = " + json.dumps(cuerpo, separators=(",", ":")) + ";\n",
        encoding="utf-8")

    log()
    log(f"  {len(lineas):,} tramos dibujados  ·  {ruta.stat().st_size/1024:,.0f} KB")
    log(f"  {ruta}")
    log("listo")


if __name__ == "__main__":
    main()
