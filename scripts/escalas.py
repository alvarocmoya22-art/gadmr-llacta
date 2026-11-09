"""Los indicadores en cada escala del territorio, y el mapa manzana a manzana.

    python -I scripts/escalas.py

Escribe:
    datos/escalas.json · .js   los tres indicadores en cada unidad de cada escala
    datos/mapa.js              las 3.757 manzanas como trazos SVG, con su cobertura
                               y los limites de cada escala

LA PLATAFORMA MANDA. Es la division con la que de verdad se trabaja en el
municipio, y la parroquia es demasiado gruesa para decidir: Lizarzaburu son
63.647 habitantes y 1.291 ha, un territorio sobre el que no se toma ninguna
decision concreta. Las 18 plataformas del casco parten eso en piezas del
tamano de una intervencion.

La parroquia se queda como segunda escala porque es la unica que cubre el
canton entero: las plataformas solo llegan al casco, y sin la parroquia el
area rural desapareceria del observatorio sin que nadie lo notara.

LA UNIDAD SE ASIGNA POR GEOMETRIA, NO POR UN CODIGO. Las manzanas del INEC
traen `parroquia_cod`, pero toda la ciudad comparte el 060150: 2.921 de las
3.757. Por el codigo, las cinco parroquias urbanas serian una sola cosa. Cada
manzana va a la unidad que contiene su punto representativo.

LAS PLATAFORMAS SE COMPRUEBAN SOLAS. `poblacion.json` del visor ya publica la
poblacion de cada plataforma, calculada aparte con el mismo reparto
dasimetrico por edificios. Aqui se vuelve a calcular sumando manzanas, y las
dos cifras tienen que cuadrar: si no cuadran, una de las dos esta mal y el
informe lo dice en vez de callarlo.

EL MAPA NO NECESITA UNA BIBLIOTECA DE MAPAS. Las manzanas se proyectan a
metros, se simplifican y salen como trazos SVG con las coordenadas redondeadas.
Pesa lo que pesa un dibujo, se abre sin servidor y no pide mosaicos a nadie. La
cobertura de cada manzana viaja como un entero de 0 a 100, uno por indicador.

DOS ENCUADRES, UN SOLO DIBUJO. El canton mide 99.782 ha y la ciudad cabe en una
esquina. Se calculan las dos cajas y la pagina cambia de una a otra moviendo el
viewBox.

LA TRANSFORMACION SE ANCLA AL CANTON. Si cada mapa se encuadrara con sus
propios datos, los limites y los rotulos solo caerian bien en uno. Con el
canton de referencia, el mapa de manzanas y el de la red vial quedan
superpuestos y cambiar de vista no mueve nada.
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

# Las escalas, en el orden en que se ofrecen. La primera es la que sale puesta.
ESCALAS = [
    {
        "clave": "plataformas",
        "nombre": "Plataformas",
        "archivo": "plataformas.geojson",
        "nota": "18 del casco urbano · la división con la que se trabaja",
        "cubre": "solo el casco urbano",
    },
    {
        "clave": "parroquias",
        "nombre": "Parroquias",
        "archivo": "parroquias_canton.geojson",
        "nota": "17 del cantón · la única escala que llega al área rural",
        "cubre": "todo el cantón",
    },
]


def log(m=""):
    print(str(m).encode("ascii", "replace").decode("ascii"), flush=True)


def sin_tildes(s: str) -> str:
    pares = "áaéeíióoúuüuññ"
    for i in range(0, len(pares), 2):
        s = s.replace(pares[i], pares[i + 1]).replace(pares[i].upper(), pares[i + 1].upper())
    return s


def rotulo(clave_escala: str, fila) -> str:
    """El nombre que se lee. Las plataformas vienen como «PLATAFORMA F»."""
    if clave_escala == "plataformas":
        return f"Plataforma {fila['clave']}"
    return str(fila["nombre"])


def subtitulo(clave_escala: str, fila) -> str:
    return "casco urbano" if clave_escala == "plataformas" else str(fila.get("tipo", ""))


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
    ficha = RAIZ / "datos" / "indicadores.json"
    if not ficha.exists():
        log("no existe datos/indicadores.json; corre antes scripts/indicadores.py")
        sys.exit(1)
    inds = json.loads(ficha.read_text(encoding="utf-8"))["indicadores"]

    log("=== LLACTA  ·  escalas y mapa ===")
    log(f"  indicadores: {', '.join(i['clave'] for i in inds)}")
    log()

    man = gpd.read_file(DATOS / "manzanas.geojson").to_crs(M)
    man["_area"] = man.geometry.area
    man["_pob"] = man["poblacion"].fillna(0)
    eq = gpd.read_file(DATOS / "equipamientos.geojson").to_crs(M)
    pob_total = float(man["_pob"].sum())
    log(f"  manzanas {len(man):,}  ·  {pob_total:,.0f} hab  ·  equipamientos {len(eq):,}")

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
        # Tiene que reproducir lo que calculo indicadores.py por su cuenta: si
        # no cuadra, una de las dos paginas esta mintiendo.
        dif = abs(total - ind["alcanzados"]) / max(ind["alcanzados"], 1) * 100
        log(f"  {ind['clave']:<28} {round(total):>9,} hab   "
            + ("ok" if dif < 0.01 else f"NO CUADRA ({dif:.3f} %)"))
    log()

    # --------------------------------------------- la transformacion del mapa
    par = gpd.read_file(DATOS / "parroquias_canton.geojson").to_crs(M)
    cajaC = par.total_bounds
    urb = par[par["tipo"] == "urbana"]
    cajaU = urb.total_bounds if len(urb) else cajaC
    x0, y0 = cajaC[0], cajaC[3]
    escala = LADO / max(cajaC[2] - cajaC[0], cajaC[3] - cajaC[1])

    # ----------------------------------------------------- cada escala
    salida, limites = [], {}
    censo_plat = {}
    try:
        censo_plat = json.loads(
            (DATOS / "poblacion.json").read_text(encoding="utf-8")
        ).get("plataformas", {})
    except Exception:
        log("  AVISO: no se pudo leer poblacion.json; sin comprobacion cruzada.")

    for esc in ESCALAS:
        gdf = gpd.read_file(DATOS / esc["archivo"]).to_crs(M).reset_index(drop=True)
        gdf["_rot"] = [rotulo(esc["clave"], f) for _, f in gdf.iterrows()]
        gdf["_sub"] = [subtitulo(esc["clave"], f) for _, f in gdf.iterrows()]

        # cada manzana, a su unidad
        pts = man[["geometry"]].copy()
        pts["geometry"] = pts.geometry.representative_point()
        casa = gpd.sjoin(
            pts, gdf[["_rot", "_sub", "geometry"]], how="left", predicate="within"
        ).drop(columns="index_right")
        # Una manzana puede caer en dos poligonos si se solapan; se queda el
        # primero, y el aviso de abajo dice cuantas veces paso.
        casa = casa[~casa.index.duplicated(keep="first")]
        col = f"_u_{esc['clave']}"
        man[col] = casa["_rot"].reindex(man.index).values

        # cuantos equipamientos hay DENTRO de cada unidad
        eqp = gpd.sjoin(
            eq, gdf[["_rot", "geometry"]], how="left", predicate="within"
        ).drop(columns="index_right")
        eqp = eqp[~eqp.index.duplicated(keep="first")]
        inventario = {}
        for ind in inds:
            n = ind["norma"]
            s = eqp[
                (eqp["tipo"].map(sin_tildes) == sin_tildes(n["uso"]))
                & (eqp["tipologia"] == n["tipologia"])
            ]
            inventario[ind["clave"]] = s.groupby("_rot").size().to_dict()
        total_eq = eqp.groupby("_rot").size().to_dict()

        unidades, cuadre = [], []
        for nombre, g in man.groupby(col):
            fila = gdf[gdf["_rot"] == nombre].iloc[0]
            pob = float(g["_pob"].sum())
            valores = {}
            for ind in inds:
                alc = float((g["_pob"] * g[ind["clave"]]).sum())
                cuantos = int(inventario[ind["clave"]].get(nombre, 0))
                pct = round(alc / pob * 100, 1) if pob else None
                # Tres lecturas que un mismo «0 %» confundiria:
                #   medido          hay cobertura. Puede venir de un
                #                   equipamiento vecino: el radio no se detiene
                #                   en un limite administrativo.
                #   cero_medido     hay equipamientos y aun asi no alcanzan a
                #                   nadie. Es un resultado, no un hueco.
                #   sin_inventario  no hay ni uno y nadie alcanzado. NO se
                #                   puede distinguir «no existe» de «no se
                #                   levanto», asi que no se publica como cero.
                valores[ind["clave"]] = {
                    "alcanzados": round(alc),
                    "valor_pct": pct,
                    "equipamientos": cuantos,
                    "propio": cuantos > 0,
                    "lectura": ("medido" if pct else
                                "sin_inventario" if cuantos == 0 else "cero_medido"),
                }
            u = {
                "nombre": nombre,
                "sub": str(fila["_sub"]),
                "manzanas": int(len(g)),
                "poblacion_en_manzana": round(pob),
                "area_ha": round(float(fila["area_ha"]), 1) if "area_ha" in fila else None,
                "equipamientos": int(total_eq.get(nombre, 0)),
                "indicadores": valores,
            }
            # La comprobacion cruzada de las plataformas.
            if esc["clave"] == "plataformas" and censo_plat:
                suyo = censo_plat.get(str(fila.get("clave", "")), None)
                if suyo:
                    u["poblacion_publicada"] = int(suyo["pob"])
                    cuadre.append((nombre, pob, float(suyo["pob"])))
            unidades.append(u)

        unidades.sort(key=lambda u: -u["poblacion_en_manzana"])
        mudas = [r for r in gdf["_rot"] if r not in set(man[col].dropna())]
        cubierta = sum(u["poblacion_en_manzana"] for u in unidades)

        salida.append({
            "clave": esc["clave"], "nombre": esc["nombre"], "nota": esc["nota"],
            "cubre": esc["cubre"],
            "poblacion_cubierta": cubierta,
            "pct_del_total": round(cubierta / pob_total * 100, 1),
            "unidades": unidades,
            "sin_manzanas": mudas,
        })

        # los limites y sus anclas, en la transformacion compartida
        bordes = []
        for _, fila in gdf.iterrows():
            g = fila.geometry.simplify(SIMPLIFICA * 4, preserve_topology=True)
            d = trazo(g, x0, y0, escala)
            if not d:
                continue
            # El ancla del rotulo es un punto DENTRO de la unidad, no el
            # centroide: el de Pungala —27.931 ha en forma de L— cae fuera de
            # ella y el nombre saldria flotando sobre la vecina.
            q = fila.geometry.representative_point()
            bordes.append({
                "d": d, "n": fila["_rot"], "t": fila["_sub"],
                "x": round((q.x - x0) * escala), "y": round((y0 - q.y) * escala),
            })
        limites[esc["clave"]] = bordes

        # ---------------------------------------------------------- informe
        log(f"  === {esc['nombre']} ===  {len(unidades)} unidades  ·  "
            f"{cubierta:,.0f} hab ({cubierta/pob_total*100:.1f} % de lo medido)  ·  "
            f"{esc['cubre']}")
        log(f"  {'unidad':<24} {'manz':>5} {'hab':>8} {'equip':>6}"
            + "".join(f" {i['clave'][11:18]:>8}" for i in inds))
        log(f"  {'-'*24} {'-'*5} {'-'*8} {'-'*6}" + "".join(" " + "-"*8 for _ in inds))
        for u in unidades:
            celdas = ""
            for i in inds:
                v = u["indicadores"][i["clave"]]
                celdas += ("    s/inv" if v["lectura"] == "sin_inventario"
                           else f" {(v['valor_pct'] or 0):>6.1f}%" + ("" if v["propio"] else "*"))
            log(f"  {u['nombre']:<24} {u['manzanas']:>5} "
                f"{u['poblacion_en_manzana']:>8,} {u['equipamientos']:>6}" + celdas)
        if mudas:
            log(f"  sin ninguna manzana: {', '.join(mudas)}")

        if cuadre:
            peor = max(cuadre, key=lambda c: abs(c[1] - c[2]) / max(c[2], 1))
            dif = abs(peor[1] - peor[2]) / max(peor[2], 1) * 100
            tot_a = sum(c[1] for c in cuadre)
            tot_b = sum(c[2] for c in cuadre)
            log()
            log("  COMPROBACION CRUZADA contra poblacion.json del visor, que calculo")
            log("  lo mismo por su cuenta con el mismo reparto por edificios:")
            log(f"    sumando manzanas  {tot_a:>10,.0f}")
            log(f"    publicado         {tot_b:>10,.0f}   dif {abs(tot_a-tot_b)/tot_b*100:.2f} %")
            log(f"    peor unidad: {peor[0]}  {peor[1]:,.0f} vs {peor[2]:,.0f}  ({dif:.1f} %)")
        log()

    # ---------------------------------------------------------------- mapa
    simple = man.geometry.simplify(SIMPLIFICA, preserve_topology=True)
    claves = [e["clave"] for e in ESCALAS]
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
            # En qué unidad cae, en cada escala. Es lo que la ficha del mapa
            # enseña al pasar por encima, y tiene que seguir a la escala
            # elegida o diria «Lizarzaburu» mientras se miran plataformas.
            "u": [
                (str(fila[f"_u_{c}"]) if fila[f"_u_{c}"] == fila[f"_u_{c}"] else None)
                for c in claves
            ],
        })

    def caja_svg(b):
        return [round((b[0] - x0) * escala), round((y0 - b[3]) * escala),
                round((b[2] - b[0]) * escala), round((b[3] - b[1]) * escala)]

    mapa = {
        "generado": hoy,
        "indicadores": [i["clave"] for i in inds],
        "escalas": claves,
        "viewBox": {"canton": caja_svg(cajaC), "ciudad": caja_svg(cajaU)},
        # Metros de terreno por unidad del viewBox. Sin esto la pagina no puede
        # dibujar una barra de escala de verdad, y una inventada es peor que
        # ninguna.
        "m_por_unidad": round(1 / escala, 4),
        "manzanas": manzanas,
        "limites": limites,
    }

    destino = RAIZ / "datos"
    destino.mkdir(exist_ok=True)
    cuerpo = {
        "generado": hoy,
        "poblacion_medida": round(pob_total),
        "escalas": salida,
        "indicadores": [{"clave": i["clave"], "nombre": i["nombre"],
                         "radio_m": i["radio_m"]} for i in inds],
    }
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

    log(f"  mapa: {len(manzanas):,} manzanas  ·  "
        + "  ·  ".join(f"{len(v)} {k}" for k, v in limites.items())
        + f"  ·  {(destino / 'mapa.js').stat().st_size/1024:,.0f} KB")
    log(f"  {destino / 'escalas.json'}")
    log("listo")


if __name__ == "__main__":
    main()
