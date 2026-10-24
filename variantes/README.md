# Propuestas de distribución de la planta baja

Hay 10 propuestas: 5 que **mantienen la cochera** (C1 a C5) y 5 que **la eliminan** (S1 a S5). Todas cumplen lo pedido el 24/10/2026:

- un dormitorio con cama de matrimonio (150 × 200) y armario;
- una cocina;
- un baño con plato de ducha;
- la máxima zona diáfana posible y sin pasillos.

Todas mantienen el muro central, la chimenea, la puerta al patio y la escalera en L. El primer piso sigue diáfano en todas.

Cada propuesta es un YAML que parte de `../casa.yaml` (`base: casa.yaml`) y solo redefine la planta baja: tabiques, puertas, estancias y muebles. Se genera así:

```bash
python tools/generar_sh3d.py variantes/c1.yaml      # -> variantes/salida/c1.sh3d y c1.md
```

En `salida/` hay, para cada propuesta, el `.sh3d`, el plano de cada planta (`<id>_planta_baja.png`), una vista 3D de la planta baja (`<id>_3d.png`) y las superficies (`<id>.md`).

## Reglas de Edu (24/10/2026)

Estas reglas se suman a los requisitos de arriba y se aplican todas a la vez:

1. El **salón** va junto a la **chimenea**.
2. El **dormitorio** va **detrás de la cochera**, al fondo derecha, con **ventana al patio**. Esa ventana es nueva, en el muro del fondo.
3. La **cocina**, el **baño** y el **salón** van en la **zona izquierda**.

Las propuestas **R1, R2 y R3** cumplen estas reglas. Las C y las S son anteriores y no las cumplen todas.

| Id | Propuesta | Salón | Cocina y comedor | Baño | Dormitorio | Otros |
|---|---|---|---|---|---|---|
| R1 | Con cochera: cocina delante y baño en el centro | 17,1 | 29,1 | 4,0 | 11,6 | Cochera 24,6 (4,9 m de fondo) |
| R2 | Con cochera: baño delante y cocina en línea | 15,9 | 30,4 | 4,0 | 11,6 | Cochera 24,6 (4,9 m de fondo) |
| R3 | Sin cochera: recibidor y estudio delante | 17,1 | 29,1 | 4,0 | 12,8 | Recibidor y estudio 23,4 |

En R1 y R2, la escalera y el dormitorio se alcanzan por el lateral de la cochera, en una franja de 1 m junto al coche. Es el precio de mantener la cochera con el dormitorio detrás. R3 lo evita convirtiendo la cochera en recibidor.

## Resumen de C y S (m² útiles)

| Id | Propuesta | Dormitorio | Baño | Zona de día | Cochera / otros |
|---|---|---|---|---|---|
| C1 | Dormitorio delante y baño bajo la escalera | 10,1 | 3,3 (bajo escalera) | 40,1 | Cochera 34,8 |
| C2 | Baño delante y dormitorio al fondo con chimenea | 10,4 | 4,0 | 35,9 | Cochera 36,2 + despensa 4,3 |
| C3 | Cocina abierta delante y baño bajo la escalera | 10,4 | 3,3 (bajo escalera) | 39,9 | Cochera 34,8 |
| C4 | Dormitorio con baño en suite y cocina junto al patio | 10,1 | 5,7 (en suite) | 34,4 | Cochera 36,2 + despensa 4,3 |
| C5 | Dormitorio semiabierto tras el armario | 7,9 | 3,3 (bajo escalera) | 42,4 | Cochera 34,8 |
| S1 | Salón en la antigua cochera | 11,3 | 3,3 (bajo escalera) | 50,2 + 23,5 | — |
| S2 | Dormitorio en la antigua cochera | 10,4 | 3,3 (bajo escalera) | 50,2 | Estar o estudio 24,4 |
| S3 | Suite al fondo con baño en suite | 12,5 | 3,3 (en suite, bajo escalera) | 50,2 + 22,3 | — |
| S4 | Cocina en la antigua cochera | 10,4 | 6,3 | 39,9 + 16,2 | Lavadero o estar 13,8 |
| S5 | Loft: todo abierto salvo dormitorio y baño | 10,1 | 3,3 (bajo escalera) | 40,1 + 34,8 | — |

## Notas comunes

- **Escalera**: tiene forma de L en el plano, pegada al muro central por el lado derecho. El tramo largo va de la mitad de la casa al muro del fondo y el pie, de 2 peldaños, sale hacia la derecha. Son 20 peldaños de unos 17 cm de alto y 27 cm de fondo. Los peldaños son losas y no llegan al suelo, así que el hueco de debajo queda libre.
- **Baño bajo la escalera** (C1, C3, C5, S1, S2, S3 y S5): ocupa 1,75 × 1,89 m. Una parte queda bajo los últimos peldaños, donde hay más de 2 m de altura libre, y el resto sale hacia la derecha de la escalera. La ducha (90 × 80) va en la zona más alta. La puerta, en el muro central, está donde la escalera ya deja más de 2 m libres. Delante queda un trastero bajo, aprovechando los primeros peldaños.
- **Con cochera**: la escalera arranca desde la cochera. La casa se comunica con ella por una puerta en el muro central, delante de la escalera. Queda un carril de unos 3 m de ancho para el coche, de 1,80 × 4,30 en el plano.
- **Sin cochera**: el portón de la cochera pasa a ser un ventanal y el muro central se abre delante con huecos de 2,2 a 3 m.
- Las posiciones de muebles y tabiques son orientativas y se ajustan en el YAML de cada propuesta.
