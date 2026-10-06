# Guía del archivo de joystick (`*_gss_joystick_*.csv`)

Este documento explica cómo leer e interpretar cada columna del archivo CSV que registra el movimiento del joystick cuadro a cuadro durante la tarea GSS.

Cada fila representa una **lectura instantánea del stick** en un momento dado, no necesariamente una respuesta completa.

## Columnas

### `timestamp_ms`
Marca de tiempo en milisegundos, tomada desde el inicio del programa (reloj interno de pygame). Sirve para ordenar los eventos y calcular tiempos de reacción relativos entre filas.

### `trial_index`
Número de ensayo (trial) al que pertenece esa lectura. Se incrementa cada vez que se confirma una respuesta.

### `block`
Nombre del bloque o fase de la tarea en la que se tomó la lectura (por ejemplo, prácticas de color, prácticas de Stroop, bloques de velocidad/precisión, bloques de prueba, etc.).

### `x_raw` y `y_raw`
Posición cruda del stick en cada eje, tal como la reporta el controlador físico. El rango normal es de **-1.0 a 1.0**, donde `0.0` significa que el stick está centrado (en reposo).

**Cómo interpretar el signo:**

| Eje | Valor negativo | Valor positivo |
|---|---|---|
| `x_raw` | Izquierda | Derecha |
| `y_raw` | Arriba | Abajo |

> Nota: el eje vertical está invertido respecto a la intuición matemática habitual: valores negativos de `y_raw` corresponden a "arriba" y positivos a "abajo".

Ejemplo: `x_raw = -0.8`, `y_raw = 0.1` → el stick está bastante inclinado a la izquierda y ligeramente hacia abajo.

### `magnitude`
Indica **qué tan lejos del centro** está el stick, sin importar la dirección. Se obtiene combinando `x_raw` y `y_raw` (distancia euclidiana al centro).

- `0` → stick completamente centrado.
- Valores cercanos a `1` → stick desplazado al máximo en esa dirección.
- Es útil para saber si un movimiento fue "fuerte" o apenas perceptible, independientemente de hacia dónde apuntaba.

### `angle_deg`
Ángulo (en grados, de `0°` a `360°`) hacia el que apunta el stick, calculado a partir de `x_raw` y `y_raw`. Funciona como una brújula:

- **0° ≈ arriba**
- **90° ≈ derecha**
- **180° ≈ abajo**
- **270° ≈ izquierda**

Los valores intermedios representan direcciones diagonales (por ejemplo, ~45° sería "arriba-derecha").

### `direction`
Es la **etiqueta categórica** que resume `angle_deg` y `magnitude` en una de cinco posibilidades:

| Valor | Criterio |
|---|---|
| `rest` | El stick está prácticamente centrado (`magnitude` muy baja, menor a 0.1), sin importar el ángulo. |
| `up` | El ángulo cae fuera de los rangos de abajo (zona alrededor de 0°/360°). |
| `right` | Ángulo entre 45° y 135° (zona alrededor de 90°). |
| `down` | Ángulo entre 135° y 225° (zona alrededor de 180°). |
| `left` | Ángulo entre 225° y 315° (zona alrededor de 270°). |

> Importante: esta clasificación usa un umbral de reposo distinto al que determina si un movimiento cuenta como "respuesta" dentro de la tarea. Es posible ver una `direction` distinta de `rest` en filas que no llegaron a registrarse como respuesta oficial del participante, porque esta columna solo describe el movimiento físico del stick, no la decisión de la tarea.

### `event`
Marca el **tipo de momento** que representa esa fila dentro del flujo del ensayo. Puede tomar tres valores:

| Valor | Cuándo se registra |
|---|---|
| `stim_onset` | En el instante exacto en que aparece el estímulo en pantalla (inicio del ensayo o reinicio tras cambiar a pantalla completa). En estas filas `x_raw` y `y_raw` se guardan como `0.0` porque marcan el punto de referencia temporal, no una lectura del stick. |
| *(vacío)* | Lectura de rutina tomada en cada cuadro mientras se espera la respuesta del participante. Es el "muestreo continuo" del movimiento del stick durante el ensayo. |
| `response_registered` | El cuadro exacto en el que el sistema detectó y aceptó una respuesta válida (el stick salió de la zona muerta y se clasificó en una dirección válida para la tarea). |

En resumen: busca `stim_onset` para saber cuándo empezó el ensayo, filas vacías para ver la trayectoria completa del movimiento, y `response_registered` para identificar el instante preciso de la respuesta usada para calcular el tiempo de reacción y la corrección del ensayo.
