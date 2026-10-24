# Estado del proyecto

_Última actualización: 24/10/2026_

## Objetivo

Hacerse una idea de las opciones para distribuir la casa (planta baja y primer piso) y poder crear y redimensionar estancias con facilidad hasta encontrar la distribución óptima. Las medidas parten del catastro, porque todavía no hay medidas reales.

## Plan

| # | Paso | Estado |
|---|---|---|
| 1 | Plano base a partir del catastro: contorno, m², dos plantas, muro central, escalera, huecos de fachada y patio | ✅ Hecho (pendiente de confirmar supuestos) |
| 2 | Elegir la forma de modelar: revisar el MCP de Sweet Home 3D que hay en `F:\ws\mcp\sweethome3d-mcp-server` o seguir con `casa.yaml` y el generador | ⏳ Pendiente: no he podido acceder a ese ordenador |
| 3 | Probar distribuciones alternativas y compararlas por m² | 🔶 Hechas 10 propuestas de planta baja (5 con cochera y 5 sin ella) en [`variantes/`](../variantes/README.md). Falta que Edu elija |
| 4 | Añadir los pilares cuando se conozcan y ajustar lo que choque | ⏳ Pendiente de datos |

## Lo que está hecho (paso 1)

### Datos del catastro

Están en [`datos/catastro/parcela_7806511YJ3070N.json`](../datos/catastro/parcela_7806511YJ3070N.json).

| Dato | Valor |
|---|---|
| Dirección | CL Purísima Alpatro 17, Garroferal, 03788 Vall de Gallinera (Alicante) |
| Uso | Industrial (almacén) |
| Año de construcción | 1910 |
| Superficie de parcela | 251 m² |
| Superficie construida | 224 m² = 112 m² en planta baja + 112 m² en planta primera |

La **geometría de la parcela** (14 vértices en UTM 30N) se ha descargado del servicio INSPIRE del catastro y el área calculada cuadra (251,3 m²). La geometría del **edificio** dentro de la parcela no se ha podido descargar, porque el servicio devolvió un binario que no se pudo leer. Por eso el fondo edificado se ha calculado como se explica abajo.

### Medidas que salen

| Medida | Valor | Origen |
|---|---|---|
| Ancho de fachada | 11,96 m | Lindero de la parcela (catastro) |
| Fondo de la parcela | 21,13 m | Catastro |
| Fondo edificado | 9,42 m | **Calculado**: el fondo con el que la parte edificada suma 112 m² |
| Útil interior por planta | ≈ 95,5 m² | Con muros exteriores de 40 cm |
| Resto de parcela (patio) | ≈ 139 m² | Parcela menos edificio |

Las superficies de cada estancia están en [`salida/superficies.md`](../salida/superficies.md).

### Modelo actual (`casa.yaml`)

**Planta baja** (altura 3,20 m, aprox):

- Muro central existente de 30 cm en `x = 6,50 m`, que va de la fachada al fondo (posición ajustada por Edu el 24/10).
- **Zona izquierda (entrada)**: unos 51 m². La puerta al patio está en el muro del fondo de esta zona, cerca del muro central (x = 4,80 m), y es la única puerta exterior trasera. **Chimenea** adosada al muro izquierdo, en la esquina del fondo (unos 0,45 × 1,80 m). Ambas posiciones las marcó Edu el 24/10 y están estimadas sobre el plano.
- **Cochera** a la derecha: unos 36,2 m² (sin contar la escalera).
- **Escalera en L**, tal y como se ve en el plano. Va en el **lado de la cochera**, pegada al muro central. El tramo largo, de 16 peldaños, sube desde la mitad de la casa hasta el muro del fondo. En su arranque tiene una meseta y un pie de 2 peldaños hacia la derecha. Son 20 peldaños de unos 17 cm con huella de 27 cm. Es un objeto 3D con peldaños tipo losa, que dejan libre el hueco de debajo (más de 2 m de altura libre a partir de y ≈ 7,1 m), y abre automáticamente el hueco en el forjado del primer piso. La forma de L la corrigió Edu el 24/10.
- Fachada: ventanuco, portón izquierdo (2,00 m) y portón de la cochera (2,45 m). Posiciones medidas sobre la foto, aproximadas.

**Primer piso** (altura 3,00 m hasta la cubierta, aprox; forjado de 25 cm):

- Planta diáfana de unos 90 m², sin contar el hueco de la escalera.
- Las dos ventanas pequeñas de la fachada.

Planos renderizados por Sweet Home 3D: [`salida/plano_planta_baja.png`](../salida/plano_planta_baja.png) y [`salida/plano_primer_piso.png`](../salida/plano_primer_piso.png). Vistas 3D: [`salida/vista_3d.png`](../salida/vista_3d.png) (exterior) y [`salida/vista_3d_planta_baja.png`](../salida/vista_3d_planta_baja.png) (planta baja sin el primer piso, para ver la escalera).

### Validación

El `.sh3d` generado se ha abierto con el motor de **Sweet Home 3D 7.5** (`tools/ValidarSH3D.java`). Carga sin errores los dos niveles, 11 muros, 6 huecos, las estancias con sus m² y la brújula orientada al norte real. Los PNG de `salida/` son el plano tal y como lo dibuja Sweet Home 3D. Las vistas 3D se han renderizado con el motor de fotos de Sweet Home 3D (`tools/Render3D.java`); no se han probado en la ventana 3D de la aplicación de escritorio. El archivo incluye una cámara aérea inicial mirando la casa desde la calle.

## Supuestos y dudas abiertas

Cada punto debería confirmarse o corregirse:

1. **Discrepancia del patio.** Según el catastro, el edificio ocupa 112 m² y deja unos 139 m² libres en la parcela. Edu calcula que el patio interior mide unos **32 m²**. Hay tres posibilidades:
   - el edificio es más profundo de lo que dice el catastro;
   - parte del resto de la parcela es otra construcción o corral;
   - el patio de 32 m² es solo una parte del espacio libre.

   Para corregirlo basta con poner el fondo real en `edificio.fondo` de `casa.yaml`, en lugar de `auto`.
2. **Lado de la fachada.** Se ha supuesto que la fachada a la calle es el lindero **oeste** de la parcela (vértices 10 → 9 del catastro), porque es el lado recto de unos 12 m. Si fuera el este, se cambia `parcela.fachada` a `[1, 14]` o el par que corresponda.
3. **Alturas** de planta (3,20 y 3,00 m) y grosor de los muros (40 cm): estimadas.
4. **Posición del muro central** (`x = 6,50 m`): estimada a partir de la foto y ajustada por Edu, sin medir.
5. **Escalera**: en L, con peldaños cómodos de unos 17 cm. El reparto se cambia con `peldanos_pie` y el lado del pie con `giro` en `casa.yaml`. En las propuestas con cochera se sube desde la cochera.
6. **Pilares**: no se conocen. Se añadirán cuando Edu tenga los datos.
7. **Cubierta**: no está modelada; el primer piso llega hasta 3,00 m.

## Limitaciones del modelo

- Puertas y ventanas son cajas de color (marrón para puertas, azul para ventanas) que abren el hueco en el muro. Se pueden sustituir en Sweet Home 3D por modelos del catálogo.
- Si se edita el `.sh3d` a mano en Sweet Home 3D y luego se vuelve a generar desde `casa.yaml`, **se pierden los cambios manuales**. Lo recomendable es tratar `casa.yaml` como fuente de verdad y usar Sweet Home 3D para visualizar y amueblar copias.

## Propuestas de distribución (paso 3)

El 24/10 Edu pidió al menos 5 propuestas con cochera y 5 sin ella. Todas debían tener un dormitorio de matrimonio con armario, una cocina y un baño con plato de ducha, ser lo más diáfanas posible y no tener pasillos. Se permitía aprovechar el hueco de debajo de la escalera. Están en [`variantes/README.md`](../variantes/README.md), con una tabla comparativa de m², y cada una tiene su `.sh3d`, planos y vista 3D en `variantes/salida/`. Galería para comparar: https://claude.ai/artifact/7svxjR78qA7Gcsaqo2ihX8 Después, Edu fijó unas **reglas**: salón junto a la chimenea, dormitorio detrás de la cochera con ventana al patio, y cocina, baño y salón en la zona izquierda. Con ellas se hicieron **R1, R2 y R3**, descritas en `variantes/README.md`. **Pendiente: que Edu elija una o varias para seguir trabajando**, y diseñar el primer piso, que sigue diáfano.

## Próximos pasos

1. Elegir propuesta o propuestas de planta baja y afinarlas.
2. Confirmar o corregir los supuestos de arriba, sobre todo el fondo edificado y el patio.
3. Revisar el MCP de `F:\ws\mcp\sweethome3d-mcp-server` cuando el ordenador donde está (DESKTOP-83Q2C6C) esté conectado al proyecto, y decidir si se usa o se sigue con el generador.
4. Distribuir el primer piso.
