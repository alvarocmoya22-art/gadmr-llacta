"""Los indicadores por parroquia, y el mapa de la ciudad manzana a manzana.

    python -I scripts/escalas.py

Escribe:
    datos/escalas.json · .js   los tres indicadores en cada una de las 17 parroquias
    datos/mapa.js              las 3.757 manzanas como trazos SVG, con su cobertura

POR QUE POR PARROQUIA. Una sola cifra para todo el canton promedia Lizarzaburu
—4.942 hab/km2— con Pungala —14—. Son dos territorios que no se parecen en
nada, y el promedio no describe a ninguno de los dos. Un observatorio que no
dice DONDE no esta observando: esta resumiendo.

LA PARROQUIA SE ASIGNA POR GEOMETRIA, NO POR EL CODIGO. Las manzanas del INEC
traen `parroquia_cod`, pero toda la ciudad comparte el codigo 060150: 2.921 de
las 3.757. Por el codigo, Lizarzaburu, Velasco, Veloz, Maldonado y Yaruquies
serian una sola cosa. Asi que cada manzana va a la parroquia que contiene su
punto representativo.

EL MAPA NO NECESITA UNA BIBLIOTECA DE MAPAS. Las manzanas se proyectan a metros,
se simplifican y salen como trazos SVG con las coordenadas redondeadas. Pesa lo
que pesa un dibujo, se abre sin servidor, no pide mosaicos a nadie y no hay un
`maplibre` de 800 KB para ensenar una ciudad que no se mueve. La cobertura de
cada manzana viaja como un entero de 0 a 100, uno por indicador, y la pagina
repinta el mismo trazo al cambiar de indicador sin volver a pedir nada.

DOS ENCUADRES, UN SOLO DIBUJO. El canton mide 99.782 ha y la ciudad cabe en una
esquina: un mapa del canton entero ensena un borron. Se calculan las dos cajas
—canton y ciudad— y la pagina cambia de una a otra moviendo el viewBox. No se
dibuja nada dos veces.
"""
import json
import sys
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
VISOR = RAIZ.parent / "gadmr-visor-territorio"
DATOS = VISOR / "public" / "datos"

M = 32717
SEGMENTOS = 64
SIMPLIFICA = 6      # metros; por debajo de esto una manzana no cambia de forma
LADO = 2000         # unidades del viewBox: resolucion suficiente, enteros cortos


def log(m=""):
    print(str(m).encode("ascii", "replace").decode("ascii"), flush=True)


def cargar_indicadores() -> list:
    ruta = RAIZ / "datos" / "indicadores.json"
    if not ruta.exists():
        log("no existe datos/indicadores.json; corre antes scripts/indicadores.py")
        sys.exit(1)
    return json.loads(ruta.read_text(encoding="utf-8"))["indicadores"]


def sin_tildes(s: str) -> str:
    pares = "áaéeíióoúuüuññ"
    for i in range(0, len(pares), 2):
        s = s.replace(pares[i], pares[i + 1]).replace(pares[i].upper(), pares[i + 1].upper())
    return s


def trazo(geom, x0, y0, escala) -> str:
    """Un MultiPolygon como atributo `d` de SVG, en enteros."""
    partes = []
    polis = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for poli in polis:
        for anillo in [poli.exterior] + list(poli.interiors):
            pts = []
            prev = None
            for x, y in anillo.coords:
                # La Y del SVG crece hacia abajo; la del mundo hacia arriba.
                px = round((x - x0) * escala)
                py = round((y0 - y) * escala)
                if (px, py) != prev:
                    pts.append(f"{px},{py}")
                    prev = (px, py)
            if len(pts) >= 3:
                partes.append("M" + "L".join(pts) + "Z")
    return "".join(partes)


def main() -> None:
    import geopandas as gpd

    hoy = date.today().isoformat()
    inds = cargar_indicadores()
    log("=== LLACTA  ·  escalas y mapa ===")
    log(f"  indicadores: {', '.join(i['clave'] for i in inds)}")
    log()

    man = gpd.read_file(DATOS / "manzanas.geojson").to_crs(M)
    man["_area"] = man.geometry.area
    man["_pob"] = man["poblacion"].fillna(0)
    eq = gpd.read_file(DATOS / "equipamientos.geojson").to_crs(M)
    par = gpd.read_file(DATOS / "parroquias_canton.geojson").to_crs(M)
    log(f"  manzanas {len(man):,}  ·  equipamientos {len(eq):,}  ·  parroquias {len(par)}")

    # ------------------------------------------- cada manzana, a su parroquia
    pts = man[["geometry"]].copy()
    pts["geometry"] = pts.geometry.representative_point()
    casa = gpd.sjoin(
        pts, par[["nombre", "tipo", "geometry"]], how="left", predicate="within"
    ).drop(columns="index_right")
    man["parroquia"] = casa["nombre"].values
    man["tipo_par"] = casa["tipo"].values
    sin = int(man["parroquia"].isna().sum())
    log(f"  parroquias con manzanas: {man['parroquia'].nunique()} de {len(par)}"
        + (f"  ·  {sin} manzanas fuera de toda parroquia" if sin else ""))
    log()

    # ------------------------------------------------ cobertura por indicador
    for ind in inds:
        n = ind["norma"]
        sel = eq[
            (eq["tipo"].map(sin_tildes) == sin_tildes(n["uso"]))
            & (eq["tipologia"] == n["tipologia"])
        ]
        cob = sel.geometry.buffer(ind["radio_m"], resolution=SEGMENTOS).union_all()
        frac = (man.geometry.intersection(cob).area / man["_area"]).clip(upper=1.0).fillna(0.0)
        man[ind["clave"]] = frac
        total = float((man["_pob"] * frac).sum())
        # El total tiene que reproducir el de indicadores.py, que se calculo
        # aparte: si no cuadra, una de las dos paginas esta mintiendo.
        dif = abs(total - ind["alcanzados"]) / max(ind["alcanzados"], 1) * 100
        marca = "ok" if dif < 0.01 else f"NO CUADRA ({dif:.3f} %)"
        log(f"  {ind['clave']:<28} {round(total):>9,} hab   {marca}")

    log()

    # ------------------------------------- cuantos equipamientos hay en cada una
    #
    # Sin esto la pagina mentiria. Nueve parroquias rurales dan 0,0 % en los
    # tres indicadores, y eso NO significa que en Calpi no haya una escuela:
    # significa que el inventario municipal no llega al area rural. De los 242
    # equipamientos barriales del levantamiento, 240 estan en las cinco
    # parroquias urbanas. Un cero sin esta columna al lado es una acusacion
    # contra un territorio que nadie fue a mirar.
    pe = par[["nombre", "geometry"]].rename(columns={"nombre": "_parr"})
    eqp = gpd.sjoin(eq, pe, how="left", predicate="within").drop(columns="index_right")
    inventario = {}
    for ind in inds:
        n = ind["norma"]
        sel = eqp[
            (eqp["tipo"].map(sin_tildes) == sin_tildes(n["uso"]))
            & (eqp["tipologia"] == n["tipologia"])
        ]
        inventario[ind["clave"]] = sel.groupby("_parr").size().to_dict()
    total_par = eqp.groupby("_parr").size().to_dict()

    # ------------------------------------------------------ por parroquia
    filas = []
    for nombre, g in man.groupby("parroquia"):
        ficha = par[par["nombre"] == nombre].iloc[0]
        pob = float(g["_pob"].sum())
        valores = {}
        for ind in inds:
            alc = float((g["_pob"] * g[ind["clave"]]).sum())
            cuantos = int(inventario[ind["clave"]].get(nombre, 0))
            pct = round(alc / pob * 100, 1) if pob else None
            # Tres lecturas distintas que un mismo «0 %» confundiria:
            #
            #   medido          hay cobertura, se mide y se publica. Puede venir
            #                   de un equipamiento de la parroquia vecina: el
            #                   radio no se detiene en el limite. Lican da
            #                   11,1 % en salud sin tener un subcentro propio.
            #   cero_medido     hay equipamientos de ese tipo y aun asi no
            #                   alcanzan a nadie. Es un resultado, no un hueco.
            #   sin_inventario  no hay ni uno, y nadie alcanza a nadie. Aqui NO
            #                   se puede distinguir «no existe» de «no se
            #                   levanto», y por eso no se publica como cero.
            valores[ind["clave"]] = {
                "alcanzados": round(alc),
                "valor_pct": pct,
                "equipamientos": cuantos,
                "propio": cuantos > 0,
                "lectura": (
                    "medido" if pct else
                    "sin_inventario" if cuantos == 0 else "cero_medido"
                ),
            }
        filas.append({
            "nombre": nombre,
            "tipo": str(g["tipo_par"].iloc[0]),
            "manzanas": int(len(g)),
            "poblacion_en_manzana": round(pob),
            "poblacion_censo": int(ficha["poblacion"]) if ficha["poblacion"] == ficha["poblacion"] else None,
            "area_ha": float(ficha["area_ha"]),
            "densidad_hab_km2": int(ficha["densidad_hab_km2"]) if ficha["densidad_hab_km2"] == ficha["densidad_hab_km2"] else None,
            "equipamientos": int(total_par.get(nombre, 0)),
            "indicadores": valores,
        })
    filas.sort(key=lambda f: -f["poblacion_en_manzana"])

    # Las parroquias SIN ninguna manzana se listan igual, dichas como lo que
    # son: territorio que este observatorio todavia no mide. Callarlas seria
    # dar a entender que el canton son solo las que salen.
    mudas = [p for p in par["nombre"] if p not in set(man["parroquia"].dropna())]

    log(f"  {'parroquia':<24} {'tipo':<7} {'manz':>5} {'hab':>8} {'equip':>6}"
        + "".join(f" {i['clave'][11:18]:>8}" for i in inds))
    log(f"  {'-'*24} {'-'*7} {'-'*5} {'-'*8} {'-'*6}" + "".join(" " + "-"*8 for _ in inds))
    for f in filas:
        celdas = ""
        for i in inds:
            v = f["indicadores"][i["clave"]]
            if v["lectura"] == "sin_inventario":
                celdas += "    s/inv"
            else:
                celdas += f" {(v['valor_pct'] or 0):>6.1f}%" + ("" if v["propio"] else "*")
        log(f"  {f['nombre']:<24} {f['tipo']:<7} {f['manzanas']:>5} "
            f"{f['poblacion_en_manzana']:>8,} {f['equipamientos']:>6}" + celdas)
    log()
    log("  s/inv = ni un equipamiento de ese tipo, y nadie alcanzado. No es un")
    log("          cero medido: no se puede distinguir de que nadie fue a mirar.")
    log("  *     = alcanzada desde la parroquia vecina, sin equipamiento propio.")
    if mudas:
        log(f"  sin ninguna manzana del INEC: {', '.join(mudas)}")

    # ---------------------------------------------------------------- mapa
    # LA TRANSFORMACION SE ANCLA AL CANTON, no a las manzanas.
    #
    # Si cada mapa se encuadra con sus propios datos, cada uno acaba con su
    # sistema de coordenadas y lo que se dibuje en los dos —los limites de
    # parroquia, los rotulos— solo cae bien en uno. Asi paso: «Cacha» salia en
    # mitad de la ciudad sobre el mapa de la red. Con el canton de referencia,
    # los dos mapas quedan superpuestos y cambiar de uno a otro no mueve nada.
    cajaC = par.total_bounds
    urb = par[par["tipo"] == "urbana"]
    cajaU = urb.total_bounds if len(urb) else cajaC

    x0, y0 = cajaC[0], cajaC[3]                   # esquina superior izquierda
    ancho, alto = cajaC[2] - cajaC[0], cajaC[3] - cajaC[1]
    escala = LADO / max(ancho, alto)

    simple = man.geometry.simplify(SIMPLIFICA, preserve_topology=True)
    manzanas = []
    for i, geom in enumerate(simple):
        if geom.is_empty:
            continue
        d = trazo(geom, x0, y0, escala)
        if not d:
            continue
        fila = man.iloc[i]
        manzanas.append({
            "d": d,
            "p": [int(round(float(fila[ind["clave"]]) * 100)) for ind in inds],
            "h": int(fila["_pob"]),
            "r": str(fila["parroquia"]) if fila["parroquia"] == fila["parroquia"] else None,
        })

    bordes = []
    for _, fila in par.iterrows():
        g = fila.geometry.simplify(SIMPLIFICA * 4, preserve_topology=True)
        d = trazo(g, x0, y0, escala)
        if not d:
            continue
        # El ancla del rotulo: un punto que cae DENTRO de la parroquia, no el
        # centroide. El centroide de Pungala —27.931 ha con forma de L— queda
        # fuera de ella, y el nombre saldria flotando sobre la vecina.
        q = fila.geometry.representative_point()
        bordes.append({
            "d": d, "n": fila["nombre"], "t": fila["tipo"],
            "x": round((q.x - x0) * escala), "y": round((y0 - q.y) * escala),
        })

    def caja_svg(b):
        return [round((b[0] - x0) * escala), round((y0 - b[3]) * escala),
                round((b[2] - b[0]) * escala), round((b[3] - b[1]) * escala)]

    mapa = {
        "generado": hoy,
        "indicadores": [i["clave"] for i in inds],
        "viewBox": {"canton": caja_svg(cajaC), "ciudad": caja_svg(cajaU)},
        # Metros de terreno por unidad del viewBox. Sin esto la pagina no
        # puede dibujar una barra de escala de verdad, y una barra de escala
        # inventada es peor que ninguna.
        "m_por_unidad": round(1 / escala, 4),
        "manzanas": manzanas,
        "parroquias": bordes,
    }

    destino = RAIZ / "datos"
    destino.mkdir(exist_ok=True)

    cuerpo = {"generado": hoy, "parroquias": filas, "sin_manzanas": mudas,
              "indicadores": [{"clave": i["clave"], "nombre": i["nombre"],
                               "radio_m": i["radio_m"]} for i in inds]}
    (destino / "escalas.json").write_text(
        json.dumps(cuerpo, ensure_ascii=False, indent=2), encoding="utf-8")
    (destino / "escalas.js").write_text(
        "/* Generado por scripts/escalas.py. No editar a mano. */\n"
        "window.LLACTA_ESCALAS = " + json.dumps(cuerpo, ensure_ascii=False) + ";\n",
        encoding="utf-8")
    (destino / "mapa.js").write_text(
        "/* Generado por scripts/escalas.py. No editar a mano. */\n"
        "window.LLACTA_MAPA = " + json.dumps(mapa, separators=(",", ":")) + ";\n",
        encoding="utf-8")

    log()
    log(f"  mapa: {len(manzanas):,} manzanas  ·  {len(bordes)} parroquias  ·  "
        f"{(destino / 'mapa.js').stat().st_size/1024:,.0f} KB")
    log(f"  {destino / 'escalas.json'}")
    log("listo")


if __name__ == "__main__":
    main()
