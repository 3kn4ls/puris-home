# Casa Purísima 17 – estudio de distribución

Modelo en **Sweet Home 3D** de la casa de la calle Purísima Alpatro 17, en Garroferal (Vall de Gallinera, Alicante). Referencia catastral: `7806511YJ3070N0001SS`.

El objetivo es probar distribuciones de la planta baja y del primer piso cambiando el tamaño de las estancias con facilidad hasta dar con la mejor.

> **¿Dónde estamos?** Lee [`docs/ESTADO.md`](docs/ESTADO.md). Ahí está el detalle de lo hecho, los supuestos, las dudas abiertas y los próximos pasos.

## Cómo funciona

```
casa.yaml  ──►  tools/generar_sh3d.py  ──►  salida/casa_purisima.sh3d   (se abre en Sweet Home 3D)
                                       └─►  salida/superficies.md       (m² de cada estancia)
```

1. **`casa.yaml`** es el único fichero que se edita. Define la parcela (datos del catastro), el edificio, las plantas, los huecos de fachada, los tabiques, los obstáculos (chimenea, pilares), las estancias y la escalera, todo en metros.
2. **`tools/generar_sh3d.py`** lo convierte en un `.sh3d` (un ZIP con `Home.xml`, el formato XML de Sweet Home 3D).
3. Abres `salida/casa_purisima.sh3d` en Sweet Home 3D y lo ves en 2D y 3D.

Para redimensionar una estancia basta con cambiar un número en `casa.yaml` y volver a generar el archivo.

Las **variantes** (`variantes/*.yaml`) empiezan con `base: casa.yaml` y solo redefinen lo que cambia de cada planta: tabiques, puertas, estancias y muebles. Se generan igual: `python tools/generar_sh3d.py variantes/c1.yaml`.

Para ver bien los muebles en Sweet Home 3D, activa en Preferencias la opción de ver el mobiliario en el plano "desde arriba" en lugar del icono del catálogo.

### Coordenadas en `casa.yaml`

- Origen `(0, 0)`: la esquina **exterior izquierda de la fachada**, mirando la casa desde la calle.
- `x`: a lo largo de la fachada, de izquierda a derecha.
- `y`: profundidad, desde la fachada hacia el fondo.
- Las expresiones admiten las variables `fondo` (fondo edificado), `ancho` (ancho de fachada) y `t` (grosor del muro exterior). Ejemplo: `fondo-0.80`.
- Las estancias se recortan solas contra los muros exteriores. Un hueco de escalera de la planta inferior se descuenta solo de la planta de arriba.

En Sweet Home 3D la fachada queda en la parte de abajo del plano y el fondo arriba.

## Uso

```bash
pip install -r requirements.txt
python tools/generar_sh3d.py            # genera salida/casa_purisima.sh3d y salida/superficies.md
```

Comprobación opcional con el propio motor de Sweet Home 3D: carga el archivo y dibuja el plano de cada planta en PNG. Hace falta Java 11 o superior y el `SweetHome3D.jar` de la versión portable de <https://www.sweethome3d.com>.

```bash
java -Djava.awt.headless=true -cp SweetHome3D.jar tools/ValidarSH3D.java salida/casa_purisima.sh3d salida
# muebles vistos desde arriba y recorte al edificio (necesita pantalla o xvfb-run y la carpeta lib/):
java -Dj3d.rend=noop -cp "SweetHome3D-7.5/lib/*" tools/ValidarSH3D.java variantes/salida/c1.sh3d variantes/salida c1
```

Vista 3D renderizada con el motor de fotos de Sweet Home 3D. Usa la carpeta `lib/` de la versión para Linux o de la portable, y en un servidor sin pantalla se lanza con `xvfb-run`:

```bash
java -Dj3d.rend=noop -cp "SweetHome3D-7.5/lib/*" tools/Render3D.java salida/casa_purisima.sh3d salida/vista_3d.png
# planta baja sola, vista desde arriba a la derecha:
java -Dj3d.rend=noop -cp "SweetHome3D-7.5/lib/*" tools/Render3D.java salida/casa_purisima.sh3d salida/vista_3d_planta_baja.png 1100 400 900 2.4 0.75 "Planta baja"
```

## Estructura

| Ruta | Contenido |
|---|---|
| `casa.yaml` | Modelo editable de la casa |
| `datos/catastro/` | Datos y geometría de la parcela descargados del catastro |
| `tools/generar_sh3d.py` | Generador `casa.yaml` → `.sh3d` |
| `tools/ValidarSH3D.java` | Validador y render del plano con Sweet Home 3D |
| `tools/Render3D.java` | Render 3D (fotos) con Sweet Home 3D |
| `salida/` | Archivo `.sh3d` generado, planos en PNG y superficies |
| `variantes/` | Propuestas de distribución (YAML que parten de `casa.yaml`) y sus salidas |
| `docs/ESTADO.md` | Estado del proyecto, supuestos y próximos pasos |
| `docs/fotos/` | Fotos de la fachada (Google Street View) |
