#!/usr/bin/env python3
"""Genera el fichero Sweet Home 3D (.sh3d) a partir de casa.yaml.

Uso:
    python tools/generar_sh3d.py [casa.yaml]

El .sh3d generado es un ZIP que contiene un Home.xml (formato XML de Sweet
Home 3D, legible desde la versión 5.3) y un par de modelos OBJ sencillos para
puertas y ventanas. Además se escribe un resumen de superficies en
salida/superficies.md.

Convenciones: casa.yaml usa metros con origen en la esquina exterior izquierda
de la fachada (x a lo largo de la fachada, y hacia el fondo). Sweet Home 3D
usa centímetros con la Y hacia abajo, así que X = 100*x e Y = -100*y: la
fachada queda abajo en el plano y el fondo arriba.
"""

import json
import math
import struct
import sys
import zipfile
import zlib
from pathlib import Path
from xml.sax.saxutils import quoteattr, escape

import yaml
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

RAIZ = Path(__file__).resolve().parent.parent

COLOR_PUERTA = "FF8B5A2B"
COLOR_VENTANA = "FF9EC9E0"
COLOR_SUELO_INTERIOR = "FFE8DCC8"
COLOR_SUELO_PATIO = "FFB7C9A0"
COLOR_SUELO_ESCALERA = "FFC0C0C0"

# Tipos de mueble: (color ARGB, altura por defecto en metros)
MUEBLES = {
    "cama": ("FFD9C2A0", 0.55),
    "armario": ("FF8B6B4A", 2.20),
    "ducha": ("FF8FC3DD", 0.06),
    "inodoro": ("FFF4F4F4", 0.75),
    "lavabo": ("FFF4F4F4", 0.85),
    "cocina": ("FFBDBDBD", 0.90),
    "nevera": ("FFE0E0E0", 1.85),
    "lavadora": ("FFE0E0E0", 0.85),
    "sofa": ("FF7A8FA6", 0.80),
    "mesa": ("FFA67C52", 0.75),
    "coche": ("FFB03A2E", 1.50),
    "almacen": ("FFBFAF8F", 1.00),
    "mueble": ("FFCCCCCC", 0.80),
}


# ---------------------------------------------------------------------------
# Geometría
# ---------------------------------------------------------------------------

def parcela_local(catastro, fachada):
    """Pasa los vértices UTM de la parcela al sistema local de casa.yaml.

    Devuelve (polígono local, ux, uy, origen) donde ux/uy son los vectores
    unitarios de los ejes locales expresados en UTM.
    """
    pts = [tuple(v) for v in catastro["parcela_vertices_utm"]]
    a, b = pts[fachada[0] - 1], pts[fachada[1] - 1]
    lx, ly = b[0] - a[0], b[1] - a[1]
    n = math.hypot(lx, ly)
    ux = (lx / n, ly / n)
    uy = (-ux[1], ux[0])
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    if (cx - a[0]) * uy[0] + (cy - a[1]) * uy[1] < 0:
        uy = (-uy[0], -uy[1])
    local = [((p[0] - a[0]) * ux[0] + (p[1] - a[1]) * ux[1],
              (p[0] - a[0]) * uy[0] + (p[1] - a[1]) * uy[1]) for p in pts]
    return Polygon(local).buffer(0), ux, uy, a


def recorte_fondo(parcela, fondo):
    minx, miny, maxx, _ = parcela.bounds
    return parcela.intersection(box(minx - 1, miny - 1, maxx + 1, fondo))


def fondo_por_superficie(parcela, superficie):
    lo, hi = 0.0, parcela.bounds[3]
    for _ in range(60):
        mid = (lo + hi) / 2
        if recorte_fondo(parcela, mid).area < superficie:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 2)


def evalua(valor, variables):
    """Permite expresiones sencillas en el YAML, p. ej. "fondo-0.80"."""
    if isinstance(valor, (int, float)):
        return float(valor)
    return float(eval(str(valor), {"__builtins__": {}}, variables))


def anillo(poligono):
    coords = list(poligono.exterior.coords)[:-1]
    # Sentido horario en el plano de SH3D (Y hacia abajo) = antihorario aquí
    if Polygon(coords).exterior.is_ccw is False:
        coords.reverse()
    return coords


def poligonos(geom):
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    return [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon" and g.area > 0.01]


# ---------------------------------------------------------------------------
# Contenido binario mínimo (modelo OBJ y icono PNG)
# ---------------------------------------------------------------------------

OBJ_CAJA = """# Caja unitaria usada para puertas y ventanas
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
v 0 0 1
v 1 0 1
v 1 1 1
v 0 1 1
f 1 4 3 2
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
"""


def escalera_en_l(e, variables, subida):
    """Calcula los peldaños de una escalera en L, tal y como se ve en el plano.

    El tramo largo sube hacia el fondo pegado a `x` y termina en `fin`. En su
    arranque (el extremo más cercano a la fachada) hay una meseta en la
    esquina y un tramo corto, el "pie" de la L, que sale hacia la derecha
    (o hacia la izquierda con `giro: izquierda`). Se empieza a subir por el
    extremo del pie. Devuelve (huella en planta, bloques (x0, y0, x1, y1,
    cota superior) en metros, recorrido para la flecha, nº de tabicas, tabica).
    """
    x = evalua(e["x"], variables)
    fin = evalua(e["fin"], variables)
    ancho = evalua(e["ancho"], variables)
    huella = evalua(e.get("huella", 0.27), variables)
    n_pie = int(e.get("peldanos_pie", 2))
    total = round(subida / 0.175)
    tabica = subida / total
    signo = 1 if e.get("giro", "derecha") == "derecha" else -1
    n_largo = total - 2 - n_pie            # huellas del tramo largo
    y_meseta = fin - n_largo * huella - ancho
    borde = x + ancho if signo > 0 else x
    bloques = []
    for k in range(1, n_pie + 1):          # pie: el peldaño 1 es el más alejado de la meseta
        a = borde + signo * (n_pie - k) * huella
        b = a + signo * huella
        bloques.append((min(a, b), y_meseta, max(a, b), y_meseta + ancho, k * tabica))
    bloques.append((x, y_meseta, x + ancho, y_meseta + ancho, (n_pie + 1) * tabica))  # meseta
    for j in range(1, n_largo + 1):
        y0 = y_meseta + ancho + (j - 1) * huella
        bloques.append((x, y0, x + ancho, y0 + huella, (n_pie + 1 + j) * tabica))
    huella_planta = (unary_union([box(*b[:4]) for b in bloques])
                     .buffer(0.005, join_style=2).buffer(-0.005, join_style=2).simplify(0.001))
    arranque = borde + signo * n_pie * huella
    recorrido = [(arranque - signo * 0.1, y_meseta + ancho / 2), (x + ancho / 2, y_meseta + ancho / 2),
                 (x + ancho / 2, fin - 0.1)]
    return huella_planta, bloques, recorrido, total, tabica


def obj_bloques(bloques, subida):
    """Modelo OBJ (en cm) con un bloque por peldaño.

    Cada peldaño es una losa escalonada (no llega al suelo), así el hueco de
    debajo de la escalera queda libre y se puede aprovechar.
    Ejes OBJ de Sweet Home 3D: X = X del plano, Y = altura, Z = Y del plano.
    Se añade un canto fino a la cota de llegada para que la pieza alcance el
    forjado superior y Sweet Home 3D recorte el hueco.
    """
    lineas = ["# Escalera generada por tools/generar_sh3d.py"]
    tabica = bloques[0][4]
    cajas = [(b[0], b[1], b[2], b[3], max(0.0, b[4] - tabica - 0.12), b[4]) for b in bloques]
    ultimo = bloques[-1]
    cajas.append((ultimo[0], ultimo[1], ultimo[2], ultimo[3], subida - 0.02, subida + 0.01))
    for n, (x0, y0, x1, y1, z0, z1) in enumerate(cajas):
        X0, X1 = x0 * 100, x1 * 100
        Z0, Z1 = -y1 * 100, -y0 * 100
        H0, H1 = z0 * 100, z1 * 100
        for vx, vy, vz in [(X0, H0, Z0), (X1, H0, Z0), (X1, H1, Z0), (X0, H1, Z0),
                           (X0, H0, Z1), (X1, H0, Z1), (X1, H1, Z1), (X0, H1, Z1)]:
            lineas.append(f"v {vx:.2f} {vy:.2f} {vz:.2f}")
        o = n * 8
        for cara in ((1, 4, 3, 2), (5, 6, 7, 8), (1, 2, 6, 5), (4, 8, 7, 3), (2, 3, 7, 6), (1, 5, 8, 4)):
            lineas.append("f " + " ".join(str(o + c) for c in cara))
    return "\n".join(lineas) + "\n"


def png_escalera(bloques, recorrido):
    """Icono de planta de la escalera: peldaños y flecha de subida, fondo transparente."""
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    huella = unary_union([box(*b[:4]) for b in bloques])
    minx, miny, maxx, maxy = huella.bounds
    escala = 100  # píxeles por metro
    fig = plt.figure(figsize=((maxx - minx) * escala / 100, (maxy - miny) * escala / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.axis("off")
    for x0, y0, x1, y1, _ in bloques:
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f2efe8",
                                   edgecolor="#333333", linewidth=1.2))
    xs, ys = zip(*recorrido)
    ax.plot(xs, ys, color="black", linewidth=1.2)
    ax.annotate("", xy=recorrido[-1], xytext=recorrido[-2],
                arrowprops={"arrowstyle": "-|>", "color": "black", "linewidth": 1.2})
    salida = io.BytesIO()
    fig.savefig(salida, format="png", transparent=True)
    plt.close(fig)
    return salida.getvalue()


def png_color(argb, ancho=8, alto=8):
    """PNG de un solo color, usado como icono de planta de los muebles. Se hace
    con las proporciones del mueble para que Sweet Home 3D lo pinte entero."""
    rgb = bytes.fromhex(argb[2:])
    fila = b"\x00" + rgb * ancho
    datos = zlib.compress(fila * alto)

    def chunk(tipo, contenido):
        return (struct.pack(">I", len(contenido)) + tipo + contenido
                + struct.pack(">I", zlib.crc32(tipo + contenido) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", datos) + chunk(b"IEND", b""))


def png_gris(lado=16):
    fila = b"\x00" + b"\x90" * lado
    datos = zlib.compress(fila * lado)

    def chunk(tipo, contenido):
        return (struct.pack(">I", len(contenido)) + tipo + contenido
                + struct.pack(">I", zlib.crc32(tipo + contenido) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", lado, lado, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", datos) + chunk(b"IEND", b""))


# ---------------------------------------------------------------------------
# Construcción del Home.xml
# ---------------------------------------------------------------------------

class Home:
    def __init__(self):
        self.lineas = []
        self.contador = 0

    def nuevo_id(self, prefijo):
        self.contador += 1
        return f"{prefijo}-{self.contador}"

    def elemento(self, nombre, atributos, hijos=None):
        attrs = " ".join(f"{k}={quoteattr(str(v))}" for k, v in atributos.items() if v is not None)
        if hijos:
            self.lineas.append(f"  <{nombre} {attrs}>")
            self.lineas.extend("    " + h for h in hijos)
            self.lineas.append(f"  </{nombre}>")
        else:
            self.lineas.append(f"  <{nombre} {attrs}/>")


def cm(v):
    return f"{v * 100:.1f}"


def X(x):
    return cm(x)


def Y(y):
    return cm(-y)


def puntos(coords):
    return [f"<point x={quoteattr(X(x))} y={quoteattr(Y(y))}/>" for x, y in coords]


def cargar(ruta_yaml):
    """Lee un YAML. Si tiene `base:`, parte de ese fichero y sobrescribe las
    claves de primer nivel y, dentro de `plantas`, las claves de cada planta
    con el mismo `id` (así una variante solo cambia lo que necesita)."""
    conf = yaml.safe_load(Path(ruta_yaml).read_text(encoding="utf-8"))
    if "base" not in conf:
        return conf
    base = cargar(RAIZ / conf.pop("base"))
    plantas = {p["id"]: p for p in base["plantas"]}
    for p in conf.pop("plantas", []):
        plantas[p["id"]].update(p)
    base.update(conf)
    base["plantas"] = list(plantas.values())
    return base


def generar(ruta_yaml):
    conf = cargar(ruta_yaml)
    catastro = json.loads((RAIZ / conf["parcela"]["catastro"]).read_text(encoding="utf-8"))

    parcela, ux, uy, _ = parcela_local(catastro, conf["parcela"]["fachada"])
    ed = conf["edificio"]
    t = float(ed["grosor_muro_exterior"])
    fondo = (fondo_por_superficie(parcela, ed["superficie_catastro_m2"])
             if ed["fondo"] == "auto" else float(ed["fondo"]))
    edificio = recorte_fondo(parcela, fondo)
    interior = edificio.buffer(-t, join_style=2)
    eje_muros = edificio.buffer(-t / 2, join_style=2).simplify(0.02)
    ancho_fachada = edificio.intersection(LineString([(-5, 0.01), (50, 0.01)])).length
    variables = {"fondo": fondo, "ancho": ancho_fachada, "t": t}

    h = Home()
    resumen = []
    modelos = {}

    # Brújula: ángulo del norte respecto a "arriba" del plano, en sentido horario.
    norte_x, norte_y = ux[1], uy[1]  # componentes del norte UTM en ejes locales
    norte = math.degrees(math.atan2(norte_x, norte_y)) % 360
    _, _, maxx, _ = parcela.bounds
    centro = catastro["centroide_wgs84"]
    h.elemento("compass", {
        "x": X(maxx + 2), "y": Y(fondo + 2), "diameter": "100",
        "northDirection": f"{math.radians(norte):.5f}",
        "longitude": f"{math.radians(centro['lon']):.6f}",
        "latitude": f"{math.radians(centro['lat']):.6f}",
        "timeZone": "Europe/Madrid", "visible": "true"})

    # Vista 3D aérea inicial: desde la calle, elevada, mirando hacia el fondo
    h.elemento("camera", {
        "attribute": "topCamera", "lens": "PINHOLE",
        "x": X(ancho_fachada / 2), "y": Y(-14), "z": "1400",
        "yaw": f"{math.pi:.4f}", "pitch": f"{math.pi / 5:.4f}", "fieldOfView": "1.0472"})

    # Niveles
    elevacion = 0.0
    niveles = []
    for i, planta in enumerate(conf["plantas"]):
        if i > 0:
            elevacion += float(planta["forjado"])
        h.elemento("level", {
            "id": planta["id"], "name": planta["nombre"],
            "elevation": cm(elevacion), "floorThickness": cm(planta["forjado"] or 0.12),
            "height": cm(planta["altura"]), "elevationIndex": "0"})
        niveles.append(elevacion)
        elevacion += float(planta["altura"])

    escalera_anterior = None
    for i, planta in enumerate(conf["plantas"]):
        nivel = planta["id"]
        altura = float(planta["altura"])
        resumen.append(f"\n## {planta['nombre']}\n")
        resumen.append("| Estancia | Superficie útil (m²) |\n|---|---|")

        # Huecos en muros exteriores (puertas y ventanas)
        for hueco in planta.get("huecos") or []:
            x0 = evalua(hueco["x"], variables)
            ancho = evalua(hueco["ancho"], variables)
            y_eje = t / 2 if hueco["muro"] == "fachada" else fondo - t / 2
            es_puerta = hueco["tipo"] == "puerta"
            h.elemento("doorOrWindow", {
                "id": h.nuevo_id("hueco"), "level": nivel, "name": hueco["nombre"],
                "icon": "icono.png", "model": "caja.obj",
                "x": X(x0 + ancho / 2), "y": Y(y_eje),
                "elevation": cm(evalua(hueco["elevacion"], variables)),
                "width": cm(ancho), "depth": cm(t + 0.02), "height": cm(evalua(hueco["alto"], variables)),
                "angle": "0", "color": COLOR_PUERTA if es_puerta else COLOR_VENTANA,
                "movable": "false", "doorOrWindow": "true",
                "doorOrWindowBoundToWall": "true", "wallThickness": "1", "wallDistance": "0",
                "nameVisible": "true"})

        # Muros exteriores: un muro por lado, unidos entre sí
        coords = anillo(eje_muros)
        ids = [h.nuevo_id("muro") for _ in coords]
        for k, (p, q) in enumerate(zip(coords, coords[1:] + coords[:1])):
            h.elemento("wall", {
                "id": ids[k], "level": nivel,
                "wallAtStart": ids[k - 1], "wallAtEnd": ids[(k + 1) % len(ids)],
                "xStart": X(p[0]), "yStart": Y(p[1]), "xEnd": X(q[0]), "yEnd": Y(q[1]),
                "height": cm(altura), "thickness": cm(t), "pattern": "hatchUp"})

        # Tabiques interiores
        for tab in planta.get("tabiques") or []:
            (x1, y1), (x2, y2) = ([evalua(v, variables) for v in punto]
                                  for punto in (tab["desde"], tab["hasta"]))
            h.elemento("wall", {
                "id": h.nuevo_id("tabique"), "level": nivel,
                "xStart": X(x1), "yStart": Y(y1), "xEnd": X(x2), "yEnd": Y(y2),
                "height": cm(evalua(tab.get("alto", altura), variables)),
                "thickness": cm(evalua(tab.get("grosor", 0.10), variables)),
                "pattern": "foreground"})

        # Obstáculos macizos (chimeneas, pilares...): un muro con la forma del
        # rectángulo, que además se descuenta de las estancias.
        obstaculos = []
        for obs in planta.get("obstaculos") or []:
            ox, oy, oa, of = (evalua(obs[k], variables) for k in ("x", "y", "ancho", "fondo"))
            obstaculos.append(box(ox, oy, ox + oa, oy + of))
            if oa >= of:
                inicio, fin, grosor = (ox, oy + of / 2), (ox + oa, oy + of / 2), of
            else:
                inicio, fin, grosor = (ox + oa / 2, oy), (ox + oa / 2, oy + of), oa
            h.elemento("wall", {
                "id": h.nuevo_id("obstaculo"), "level": nivel,
                "xStart": X(inicio[0]), "yStart": Y(inicio[1]), "xEnd": X(fin[0]), "yEnd": Y(fin[1]),
                "height": cm(altura), "thickness": cm(grosor), "pattern": "crossHatch"})
            h.elemento("label", {"id": h.nuevo_id("texto"), "level": nivel,
                                 "x": X(ox + oa + 0.55), "y": Y(oy + of / 2)},
                       [f"<text>{escape(obs['nombre'])}</text>"])

        # Puertas interiores, sobre tabiques: "h" = tabique paralelo a la fachada
        # (la puerta va de x a x+ancho), "v" = perpendicular (de y a y+ancho).
        for pu in planta.get("puertas") or []:
            px, py, pa = (evalua(pu[k], variables) for k in ("x", "y", "ancho"))
            vertical = pu.get("orientacion", "h") == "v"
            grosor = evalua(pu.get("grosor", 0.10), variables)
            cx, cy = (px, py + pa / 2) if vertical else (px + pa / 2, py)
            h.elemento("doorOrWindow", {
                "id": h.nuevo_id("puerta"), "level": nivel, "name": pu.get("nombre", "Puerta"),
                "icon": "icono.png", "model": "caja.obj", "x": X(cx), "y": Y(cy), "elevation": "0",
                "width": cm(pa), "depth": cm(grosor + 0.02), "height": cm(evalua(pu.get("alto", 2.03), variables)),
                "angle": f"{math.pi / 2:.5f}" if vertical else "0", "color": COLOR_PUERTA,
                "doorOrWindow": "true", "doorOrWindowBoundToWall": "true",
                "wallThickness": "1", "wallDistance": "0"})

        # Muebles (cajas de color con su nombre) para comprobar que todo cabe
        for m in planta.get("muebles") or []:
            mx, my, ma, mf = (evalua(m[k], variables) for k in ("x", "y", "ancho", "fondo"))
            color, alto = MUEBLES[m.get("tipo", "mueble")]
            color = m.get("color", color)
            px, py = max(1, round(ma * 50)), max(1, round(mf * 50))
            icono = f"color_{color}_{px}x{py}.png"
            modelos[icono] = png_color(color, px, py)
            h.elemento("pieceOfFurniture", {
                "id": h.nuevo_id("mueble"), "level": nivel, "name": m["nombre"],
                "icon": icono, "planIcon": icono, "model": "caja.obj",
                "x": X(mx + ma / 2), "y": Y(my + mf / 2),
                "elevation": cm(evalua(m.get("elevacion", 0), variables)),
                "width": cm(ma), "depth": cm(mf), "height": cm(evalua(m.get("alto", alto), variables)),
                "color": color, "nameVisible": "true"})

        # Escalera de esta planta y hueco de la escalera de la planta inferior
        escalera = None
        if planta.get("escalera"):
            siguiente = conf["plantas"][i + 1]
            subida = altura + float(siguiente["forjado"])
            escalera, bloques, recorrido, n_tabicas, tabica = escalera_en_l(
                planta["escalera"], variables, subida)
            modelos[f"escalera_{nivel}.obj"] = obj_bloques(bloques, subida)
            modelos[f"escalera_{nivel}.png"] = png_escalera(bloques, recorrido)
            minx, miny, maxx, maxy = escalera.bounds
            # Hueco en el forjado: contorno de la escalera normalizado a la pieza
            # (0,0 = esquina trasera izquierda del plano).
            camino = " ".join(
                ("M" if k == 0 else "L") + f" {(px - minx) / (maxx - minx):.4f} {(maxy - py) / (maxy - miny):.4f}"
                for k, (px, py) in enumerate(anillo(escalera))) + " Z"
            h.elemento("pieceOfFurniture", {
                "id": h.nuevo_id("escalera"), "level": nivel, "name": "Escalera",
                "icon": f"escalera_{nivel}.png", "planIcon": f"escalera_{nivel}.png",
                "model": f"escalera_{nivel}.obj",
                "x": X((minx + maxx) / 2), "y": Y((miny + maxy) / 2), "elevation": "0",
                "width": cm(maxx - minx), "depth": cm(maxy - miny), "height": cm(subida + 0.01),
                "color": "FFB0A898", "movable": "false", "staircaseCutOutShape": camino})
        descontar = unary_union([g for g in (escalera, escalera_anterior, *obstaculos) if g is not None])

        # Las estancias se reparten en orden: cada una se queda con lo que no
        # han ocupado las anteriores (así basta con un rectángulo grande al final).
        ocupado = descontar
        bajo_escalera = Polygon()
        for est in planta.get("estancias") or []:
            if "puntos" in est:
                rect = Polygon([[evalua(v, variables) for v in p] for p in est["puntos"]])
            else:
                rect = box(*(lambda x, y, a, f: (x, y, x + a, y + f))(
                    *(evalua(est[k], variables) for k in ("x", "y", "ancho", "fondo"))))
            zona = rect.intersection(interior)
            libre = ocupado
            if est.get("bajo_escalera") and escalera is not None:
                # Puede ocupar el hueco bajo la escalera
                libre = ocupado.difference(escalera.difference(bajo_escalera))
            if not libre.is_empty:
                zona = zona.difference(libre)
            if est.get("bajo_escalera") and escalera is not None:
                bajo_escalera = unary_union([bajo_escalera, zona.intersection(escalera)])
            ocupado = unary_union([ocupado, zona])
            for pol in poligonos(zona):
                h.elemento("room", {
                    "id": h.nuevo_id("estancia"), "level": nivel, "name": est["nombre"],
                    "areaVisible": "true", "floorColor": COLOR_SUELO_INTERIOR},
                    puntos(anillo(pol)))
            resumen.append(f"| {est['nombre']} | {zona.area:.1f} |")

        if escalera is not None:
            for pol in poligonos(escalera.difference(bajo_escalera)):
                h.elemento("room", {
                    "id": h.nuevo_id("escalera"), "level": nivel, "name": "Escalera",
                    "areaVisible": "false", "floorColor": COLOR_SUELO_ESCALERA},
                    puntos(anillo(pol)))
            h.elemento("polyline", {
                "id": h.nuevo_id("subida"), "level": nivel, "thickness": "3",
                "capStyle": "BUTT", "joinStyle": "MITER", "dashStyle": "SOLID",
                "startArrowStyle": "NONE", "endArrowStyle": "DELTA",
                "closedPath": "false", "color": "FF000000"},
                puntos(recorrido))
            resumen.append(f"| Escalera en L ({n_tabicas} peldaños de {tabica * 100:.1f} cm) | {escalera.area:.1f} |")
            # Altura libre bajo la escalera (para aprovechar el hueco)
            resumen.append(f"| _Bajo la escalera: más de 2,00 m libres a partir de y = "
                           f"{next((b[1] for b in bloques if b[4] - 0.20 >= 2.0), 0):.2f} m_ | |")
        if escalera_anterior is not None:
            h.elemento("polyline", {
                "id": h.nuevo_id("hueco-escalera"), "level": nivel, "thickness": "2",
                "capStyle": "BUTT", "joinStyle": "MITER", "dashStyle": "DASH",
                "startArrowStyle": "NONE", "endArrowStyle": "NONE",
                "closedPath": "true", "color": "FF000000"},
                puntos(anillo(escalera_anterior)))
            c = escalera_anterior.centroid
            h.elemento("label", {"id": h.nuevo_id("texto"), "level": nivel,
                                 "x": X(c.x), "y": Y(c.y), "angle": f"{-math.pi / 2:.4f}"},
                       ["<text>Hueco escalera</text>"])
        escalera_anterior = escalera

        resumen.append(f"| **Superficie útil interior total** | **{interior.area:.1f}** |")
        resumen.append(f"| Superficie construida (catastro) | {edificio.area:.1f} |")

        if i == 0:
            # Patio / resto de parcela y contorno de la parcela
            patio = parcela.difference(edificio)
            for pol in poligonos(patio):
                h.elemento("room", {
                    "id": h.nuevo_id("patio"), "level": nivel, "name": "Patio / resto de parcela",
                    "areaVisible": "true", "ceilingVisible": "false", "floorColor": COLOR_SUELO_PATIO},
                    puntos(anillo(pol)))
            resumen.append(f"| Patio / resto de parcela | {patio.area:.1f} |")
            h.elemento("polyline", {
                "id": h.nuevo_id("parcela"), "level": nivel, "thickness": "2",
                "capStyle": "BUTT", "joinStyle": "MITER", "dashStyle": "DASH_DOT",
                "startArrowStyle": "NONE", "endArrowStyle": "NONE",
                "closedPath": "true", "color": "FFCC0000"},
                puntos(anillo(parcela)))
            h.elemento("label", {"id": h.nuevo_id("texto"), "level": nivel,
                                 "x": X(ancho_fachada / 2), "y": Y(-1.5)},
                       ["<text>CALLE PURÍSIMA (fachada)</text>"])
            # Cotas generales
            h.elemento("dimensionLine", {"id": h.nuevo_id("cota"), "level": nivel,
                                         "xStart": X(0), "yStart": Y(0), "xEnd": X(ancho_fachada),
                                         "yEnd": Y(0), "offset": "80"})
            h.elemento("dimensionLine", {"id": h.nuevo_id("cota"), "level": nivel,
                                         "xStart": X(0), "yStart": Y(0), "xEnd": X(0),
                                         "yEnd": Y(fondo), "offset": "-80"})
            h.elemento("dimensionLine", {"id": h.nuevo_id("cota"), "level": nivel,
                                         "xStart": X(0), "yStart": Y(0), "xEnd": X(0),
                                         "yEnd": Y(parcela.bounds[3]), "offset": "-180"})

    xml = ["<?xml version='1.0' encoding='UTF-8'?>",
           f"<home version='6400' name={quoteattr(Path(conf['salida']).name)} "
           f"selectedLevel={quoteattr(conf['plantas'][0]['id'])} wallHeight='300'>"]
    # Los niveles tienen que ir antes que los elementos que los referencian
    orden = ["<camera", "<compass", "<level", "<pieceOfFurniture", "<doorOrWindow", "<wall", "<room", "<polyline", "<dimensionLine", "<label"]
    bloques = []
    actual = None
    for linea in h.lineas:
        if linea.startswith("  <") and not linea.startswith("  </"):
            actual = [linea]
            bloques.append(actual)
        else:
            actual.append(linea)
    bloques.sort(key=lambda b: next(k for k, o in enumerate(orden) if b[0].strip().startswith(o)))
    for b in bloques:
        xml.extend(b)
    xml.append("</home>")

    salida = RAIZ / conf["salida"]
    salida.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Home.xml", "\n".join(xml) + "\n")
        z.writestr("caja.obj", OBJ_CAJA)
        for nombre, contenido in modelos.items():
            z.writestr(nombre, contenido)
        z.writestr("icono.png", png_gris())

    cabecera = [
        f"# Superficies - {conf['nombre']}",
        "",
        f"Generado automáticamente por `tools/generar_sh3d.py` a partir de `{Path(ruta_yaml).name}`. No editar a mano.",
        "",
        f"- Ancho de fachada (exterior): **{ancho_fachada:.2f} m**",
        f"- Fondo edificado (exterior): **{fondo:.2f} m**"
        + (" (calculado para cuadrar con los m² del catastro)" if ed["fondo"] == "auto" else ""),
        f"- Fondo total de parcela: **{parcela.bounds[3]:.2f} m**",
        f"- Superficie de parcela: **{parcela.area:.1f} m²**",
        f"- Norte: {norte:.0f}° en sentido horario desde la parte de arriba del plano",
    ]
    resumen_md = RAIZ / conf["resumen"] if "resumen" in conf else salida.parent / "superficies.md"
    if conf.get("descripcion"):
        cabecera += ["", conf["descripcion"].strip()]
    resumen_md.write_text("\n".join(cabecera + resumen) + "\n", encoding="utf-8")
    print(f"Generado {salida.relative_to(RAIZ)} (fondo edificado {fondo:.2f} m, "
          f"fachada {ancho_fachada:.2f} m)")
    return salida


if __name__ == "__main__":
    generar(sys.argv[1] if len(sys.argv) > 1 else RAIZ / "casa.yaml")
