"""Comprueba los indicadores por caminos distintos al del calculo.

    python -I scripts/comprobar_indicadores.py

Lee `datos/indicadores.json` y vuelve a sacar cada cifra de dos maneras que no
comparten una sola linea con `indicadores.py`:

A · OVERLAY. En vez de intersecar cada manzana contra la union de las
    coberturas, se cruzan las dos capas con `gpd.overlay(how='intersection')`,
    que es otro camino geometrico entero, y se agrupa por manzana. Si las dos
    cifras coinciden, el reparto proporcional esta bien implementado.

B · CENTROIDE. La manzana cuenta entera si su punto representativo esta a menos
    del radio de algun equipamiento, y no cuenta nada si no lo esta. Es el
    metodo tosco, el que usaria cualquiera sin preocuparse por los bordes, y
    NO tiene por que coincidir: sirve de cota. Si la cifra buena se saliera
    mucho de lo que da el centroide, habria algo mal en el reparto.

QUE NO ES ESTO. No es una comprobacion independiente de verdad: la escribio
quien escribio el calculo, con las mismas bibliotecas. Comprueba la
implementacion, no el metodo. La comprobacion de verdad es volver a sacar la
cifra con CHASKI, que implementa el mismo metodo en otro lenguaje y con otro
codigo, y eso queda pendiente.
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
DATOS = RAIZ.parent / "gadmr-visor-territorio" / "public" / "datos"
M = 32717
SEGMENTOS = 64


def log(m=""):
    print(str(m).encode("ascii", "replace").decode("ascii"), flush=True)


def sin_tildes(s: str) -> str:
    pares = "áaéeíióoúuüuññ"
    for i in range(0, len(pares), 2):
        s = s.replace(pares[i], pares[i + 1]).replace(pares[i].upper(), pares[i + 1].upper())
    return s


def main() -> None:
    import geopandas as gpd

    ruta = RAIZ / "datos" / "indicadores.json"
    if not ruta.exists():
        log(f"no existe {ruta}; corre antes scripts/indicadores.py")
        sys.exit(1)
    guardado = json.loads(ruta.read_text(encoding="utf-8"))

    log("=== Comprobacion de los indicadores ===")
    log(f"  contra {ruta.name}, generado {guardado['generado']}, "
        f"metodo v{guardado['version_metodo']}")
    log()

    man = gpd.read_file(DATOS / "manzanas.geojson").to_crs(M)
    man["_fid"] = range(len(man))
    man["_area"] = man.geometry.area
    man["_pob"] = man["poblacion"].fillna(0)
    eq = gpd.read_file(DATOS / "equipamientos.geojson").to_crs(M)
    log(f"  manzanas {len(man):,}  ·  equipamientos {len(eq):,}")
    log()

    log(f"  {'indicador':<30} {'guardado':>10} {'A overlay':>10} {'dif':>8}"
        f" {'B centroide':>12}")
    log(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*8} {'-'*12}")

    peor = 0.0
    for ind in guardado["indicadores"]:
        radio = ind["radio_m"]
        sel = eq[
            (eq["tipo"].map(sin_tildes) == sin_tildes(ind["norma"]["uso"]))
            & (eq["tipologia"] == ind["norma"]["tipologia"])
        ]
        cob = gpd.GeoDataFrame(
            geometry=[sel.geometry.buffer(radio, resolution=SEGMENTOS).union_all()],
            crs=man.crs,
        )

        # --- A · overlay
        trozos = gpd.overlay(
            man[["_fid", "_pob", "_area", "geometry"]], cob, how="intersection",
            keep_geom_type=True,
        )
        if len(trozos):
            por_man = trozos.assign(a=trozos.geometry.area).groupby("_fid")["a"].sum()
            base = man.set_index("_fid")
            frac = (por_man / base["_area"]).clip(upper=1.0)
            a_total = float((base["_pob"] * frac).dropna().sum())
        else:
            a_total = 0.0

        # --- B · centroide
        pts = man.copy()
        pts["geometry"] = pts.geometry.representative_point()
        dentro = gpd.sjoin(pts[["_pob", "geometry"]], cob, how="inner", predicate="within")
        b_total = float(dentro["_pob"].sum())

        g = ind["alcanzados"]
        dif = abs(a_total - g) / g * 100 if g else 0.0
        peor = max(peor, dif)
        log(f"  {ind['clave']:<30} {g:>10,} {round(a_total):>10,} {dif:>7.3f}%"
            f" {round(b_total):>12,}")

    log()
    log(f"  peor diferencia por overlay: {peor:.3f} %")
    if peor < 0.1:
        log("  Las dos implementaciones del reparto proporcional coinciden.")
    else:
        log("  ATENCION: las dos implementaciones NO coinciden. Algo esta mal.")
    log()
    log("  La columna B no tiene que coincidir: la manzana cuenta entera o nada.")
    log("  Queda pendiente la comprobacion de verdad, con CHASKI.")


if __name__ == "__main__":
    main()
