# Estado del proyecto

_Última actualización: 24/10/2026_

## Objetivo

Hacerse una idea de las opciones para distribuir la casa (planta baja y primer piso) y poder crear y redimensionar estancias con facilidad hasta encontrar la distribución óptima. Las medidas parten del catastro, porque todavía no hay medidas reales.

## Plan

| # | Paso | Estado |
|---|---|---|
| 1 | Plano base a partir del catastro: contorno, m², dos plantas, muro central, escalera, huecos de fachada y patio | ✅ Hecho (pendiente de confirmar supuestos) |
| 2 | Elegir la forma de modelar: revisar el MCP de Sweet Home 3D que hay en `F:\ws\mcp\sweethome3d-mcp-server` o seguir con `casa.yaml` y el generador | ⏳ Pendiente: no he podido acceder a ese ordenador |
| 3 | Probar 2 o 3 distribuciones alternativas y compararlas por m² | ⏳ Pendiente |
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
- **Zona izquierda (entrada)**: unos 51 m². Al fondo, a la izquierda, tiene la puerta al patio.
- **Cochera** a la derecha: unos 37,7 m² (sin contar la escalera).
- **Escalera** de 1,00 m de ancho, junto al muro central por el **lado de la cochera**. Va desde la mitad de la casa hasta el muro del fondo y sube hacia el fondo.
- Fachada: ventanuco, portón izquierdo (2,00 m) y portón de la cochera (2,45 m). Posiciones medidas sobre la foto, aproximadas.

**Primer piso** (altura 3,00 m hasta la cubierta, aprox; forjado de 25 cm):

- Planta diáfana de unos 91 m², sin contar el hueco de la escalera.
- Las dos ventanas pequeñas de la fachada.

Planos renderizados por Sweet Home 3D: [`salida/plano_planta_baja.png`](../salida/plano_planta_baja.png) y [`salida/plano_primer_piso.png`](../salida/plano_primer_piso.png).

### Validación

El `.sh3d` generado se ha abierto con el motor de **Sweet Home 3D 7.5** (`tools/ValidarSH3D.java`). Carga sin errores los dos niveles, 11 muros, 6 huecos, las estancias con sus m² y la brújula orientada al norte real. Los PNG de `salida/` son el plano tal y como lo dibuja Sweet Home 3D. No se ha probado la vista 3D en la aplicación de escritorio.

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
5. **Escalera**: con unos 4,3 m de recorrido para salvar unos 3,45 m de altura sale muy empinada (unos 21–22 cm por peldaño). Seguramente habrá que alargarla, hacerla en L o moverla. Es una de las primeras cosas a decidir al distribuir.
6. **Pilares**: no se conocen. Se añadirán cuando Edu tenga los datos.
7. **Cubierta**: no está modelada; el primer piso llega hasta 3,00 m.

## Limitaciones del modelo

- Puertas y ventanas son cajas de color (marrón para puertas, azul para ventanas) que abren el hueco en el muro. Se pueden sustituir en Sweet Home 3D por modelos del catálogo.
- Si se edita el `.sh3d` a mano en Sweet Home 3D y luego se vuelve a generar desde `casa.yaml`, **se pierden los cambios manuales**. Lo recomendable es tratar `casa.yaml` como fuente de verdad y usar Sweet Home 3D para visualizar y amueblar copias.

## Próximos pasos

1. Confirmar o corregir los supuestos de arriba, sobre todo el fondo edificado y el patio.
2. Revisar el MCP de `F:\ws\mcp\sweethome3d-mcp-server` cuando el ordenador donde está (DESKTOP-83Q2C6C) esté conectado al proyecto, y decidir si se usa o se sigue con el generador.
3. Crear variantes de distribución (por ejemplo `variantes/a.yaml`, `variantes/b.yaml`) y comparar sus superficies.
