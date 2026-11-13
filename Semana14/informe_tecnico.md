# Informe Técnico: Almacenamiento Avanzado de Datos IoT con Adafruit IO y SQLite

**Estudiante:** Julian Gutiérrez (completar con los integrantes del grupo)
**Curso:** Internet de las Cosas (IoT) - Semana 14
**Sustentación:** Viernes 13 de noviembre de 2026, 10:30 a. m.

---

## 1. Objetivo

Guardar en un servidor local las lecturas de temperatura, humedad y luminosidad que el ESP32 publica en Adafruit IO. Un script en Python consulta los feeds, descarta los datos ya guardados y registra los nuevos en una base SQLite. El objetivo es que los datos persistan después de reiniciar el equipo y que se conserven más allá de los 30 días de historial del plan gratuito de Adafruit IO.

---

## 2. Arquitectura del sistema

```
Sensores (DHT11, LDR) -> ESP32 (MicroPython) -> Adafruit IO -> ingesta.py (API REST) -> SQLite (sensores.db) -> DB Browser
```

| Componente | Función |
|---|---|
| DHT11 y LDR | Miden temperatura, humedad y luminosidad del aula. |
| ESP32 (`main.py`) | Publica cada 15 segundos en los feeds `temperatura`, `humedad` y `luminosidad`. |
| Adafruit IO | Recibe los datos, los muestra en el dashboard y conserva 30 días en el plan gratuito. |
| `ingesta.py` | Consulta cada feed cada 30 segundos y guarda solo las lecturas nuevas. |
| `sensores.db` | Base SQLite con la tabla `lecturas`. Almacenamiento local persistente. |
| DB Browser for SQLite | Ejecuta las consultas de verificación y permite tomar capturas. |

---

## 3. Hardware y software

| Elemento | Versión o detalle |
|---|---|
| Equipo servidor | PC con Windows 11 |
| Python | 3.15.2, instalado desde python.org con la opción *Add Python to PATH* |
| Librería `requests` | Instalada con `pip`. Consulta la API REST de Adafruit IO |
| SQLite | Módulo `sqlite3` incluido en Python |
| DB Browser for SQLite | Versión: completar |
| Microcontrolador | ESP32 NodeMCU con MicroPython |

---

## 4. Diseño de la base de datos

La base se llama `sensores.db` y contiene una tabla `lecturas`. El script la crea la primera vez con `CREATE TABLE IF NOT EXISTS`, por lo que no se pierde información al reiniciar.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER (PK, AUTOINCREMENT) | Identificador local del registro. |
| `feed` | TEXT NOT NULL | Nombre del feed: `temperatura`, `humedad` o `luminosidad`. |
| `aio_id` | TEXT NOT NULL UNIQUE | Identificador del dato en Adafruit IO. Evita guardar dos veces el mismo dato. |
| `valor` | TEXT NOT NULL | Valor tal como llegó desde Adafruit IO. |
| `valor_num` | REAL | Valor numérico para cálculos. Queda NULL si no es un número. |
| `creado_en` | TEXT NOT NULL | Marca de tiempo UTC asignada por Adafruit IO. |
| `insertado_en` | TEXT NOT NULL | Marca de tiempo UTC del momento en que el script guardó el dato. |

**Índice:** `idx_feed_fecha ON lecturas(feed, creado_en)`, que acelera las consultas por feed y por rango de fechas.

**Decisiones de diseño:**

- `aio_id` es `UNIQUE` y el script usa `INSERT OR IGNORE`. Si el script vuelve a leer datos que ya existen, la base los descarta. Por eso se pueden ejecutar rondas repetidas sin duplicar información.
- Se guardan `valor` (dato original) y `valor_num` (número para cálculos).
- `creado_en` indica cuándo se midió el dato y `insertado_en` indica cuándo llegó a la base. La diferencia entre ambos permite detectar retrasos en la ingesta.

---

## 5. Script de ingesta (`ingesta.py`)

El script funciona en un bucle infinito. Cada 30 segundos consulta los tres feeds, inserta los datos nuevos y registra en consola cuántos registros se guardaron.

Partes principales:

- **Configuración por variables de entorno.** Las credenciales se pasan desde `run.bat` y no quedan escritas en el código.
- **`init_db()`:** crea la tabla y el índice si no existen.
- **`obtener_datos()`:** consume `https://io.adafruit.com/api/v2/<usuario>/feeds/<feed>/data` con un límite de 100 datos.
- **`guardar()`:** inserta cada dato con `INSERT OR IGNORE` y cuenta solo las filas realmente insertadas (`rowcount`).
- **Manejo de errores:** si falla la red, el error se registra y el script reintenta en la siguiente ronda sin detenerse.

Fragmento central:

```python
cur = conn.execute(
    """INSERT OR IGNORE INTO lecturas
       (feed, aio_id, valor, valor_num, creado_en, insertado_en)
       VALUES (?, ?, ?, ?, ?, ?)""",
    (feed, str(d["id"]), d["value"], num, d["created_at"], ahora),
)
nuevos += cur.rowcount  # 1 si se insertó, 0 si ya existía
```

---

## 6. Automatización

`run.bat` define las variables de entorno y ejecuta `ingesta.py`. Para que el script arranque al encender el equipo, se configura una tarea en el Programador de tareas de Windows con el disparador *Al iniciar el sistema*.

**Estado:** pendiente de configurar y de capturar. Sin esta tarea, el script no se reinicia solo después de un reinicio del equipo.

---

## 7. Pruebas y resultados

### 7.1 Carga inicial y rondas posteriores

En la primera ejecución el script guardó 100 registros por feed. En las rondas siguientes aparecen 2 registros nuevos por feed cada 30 segundos, porque el ESP32 envía cada 15 segundos. Una ronda con 1 registro nuevo indica que en ese intervalo solo llegó un envío a Adafruit IO.

### 7.2 Conteo por feed

En la consulta de conteo, cada feed tenía 159 registros. El primer dato es del 6 de noviembre de 2026 a las 15:12:36 UTC y el último dato de esa consulta es del 12 de noviembre a las 20:27:37 UTC. Que los tres feeds tengan la misma cantidad es normal, porque el ESP32 publica las tres variables en cada envío.

Más adelante, al revisar la base después de la interrupción, se registraron 660 filas en total (220 por feed).

### 7.3 Vista por envío

La consulta por envío agrupa los tres feeds en una sola fila por marca de tiempo. Así se verifica que temperatura, humedad y luminosidad se guardan juntas. Los valores de temperatura (29 a 31 °C) y humedad (41 a 54 %) se repiten porque el DHT11 entrega valores enteros y cambian poco en pocos segundos. Repetir el valor no implica duplicación, porque cada fila tiene una marca de tiempo distinta.

### 7.4 Control de duplicados

La consulta de control por `aio_id` debe devolver cero filas.

**Pendiente:** captura del resultado de la consulta 4 de `consultas.sql`.

---

## 8. Incidencias durante la práctica

| Incidencia | Causa | Solución o estado |
|---|---|---|
| El nombre del feed en el dashboard (`temperature`) no coincidía con el configurado (`temperatura`). | Diferencia entre el nombre visible y la key del feed. | Se verificó la key en Adafruit IO y se usó en `AIO_FEEDS`. |
| `run.bat` tenía 0 KB y Windows bloqueaba su ejecución al hacer doble clic. | El archivo se creó vacío. | Se editó con clic derecho, *Abrir con*, Bloc de notas. |
| El comando `py` no se reconocía en CMD. | Python se instaló sin la opción *Add Python to PATH*. | Se reinstaló Python con esa opción marcada. |
| La distancia del HC-SR04 aparecía como -1.0 cm en Thonny. | El sensor no recibe eco en las pruebas. | Este dato no se publica en Adafruit IO, por lo que no entra en la base. Queda como limitación del sensor. |
| Las fechas terminan en `Z` y la consola muestra hora local. | La base guarda UTC. Colombia está 5 horas detrás de UTC. | Se documenta la conversión en la exposición. |
| Las filas de consulta parecían duplicadas. | Varias filas con el mismo valor de temperatura y humedad. | Cada fila tiene marca de tiempo distinta. Se creó la consulta por envío para presentarlas agrupadas. |
| La ingesta se detuvo entre las 3:44 p. m. y las 10:11 p. m. (hora local). | Sin confirmar. Se observó que `sensores.db` aparecía dentro de una carpeta sincronizada con OneDrive, lo que pudo bloquear la escritura. | Se reinició `run.bat`. Pendiente confirmar la ruta de la base y mover la carpeta fuera de OneDrive si corresponde. |

### 8.1 Hueco en los datos

Durante la interrupción el ESP32 siguió publicando en Adafruit IO, pero la ingesta no guardó esas lecturas. El script solo recupera las últimas 100 lecturas por consulta, lo que cubre unos 25 minutos de envíos. Por eso no es posible recuperar las horas perdidas. El hueco queda registrado en la base, y el historial anterior (hasta las 3:44 p. m.) se conserva.

---

## 9. Prueba de persistencia tras reinicio

La prueba consiste en registrar el conteo antes de reiniciar, reiniciar el equipo, comprobar que la ingesta arranca sola y comparar el conteo después.

| Momento | Registros | Primer dato | Último dato | Estado |
|---|---|---|---|---|
| Antes del reinicio | Completar | 2026-11-06T15:12:36Z | Completar | Pendiente |
| Después del reinicio | Completar (debe ser igual o mayor) | 2026-11-06T15:12:36Z (no debe cambiar) | Completar (debe ser más reciente) | Pendiente |

**Pendiente:** captura del conteo antes del reinicio, captura del equipo reiniciado, conteo después del reinicio y captura del Programador de tareas con la ingesta en ejecución.

---

## 10. Conclusiones

- La ingesta funciona: lee los tres feeds de Adafruit IO y guarda solo los datos nuevos. La restricción `UNIQUE` sobre `aio_id` evita duplicados.
- La base local conserva un historial desde el 6 de noviembre de 2026, más allá de los 30 días del plan gratuito de Adafruit IO.
- Después de una interrupción de varias horas, la ingesta volvió a guardar datos nuevos al reiniciarse, y los datos anteriores siguieron en la base.
- Se identificó que el almacenamiento puede verse afectado si la base está dentro de una carpeta sincronizada, como OneDrive.

---

## 11. Limitaciones y mejoras

- **Dependencia del equipo encendido:** la ingesta solo guarda datos mientras el PC está encendido y `run.bat` está corriendo. Un reinicio o un cierre de la ventana genera un hueco.
- **Ventana de recuperación:** el script solo obtiene 100 datos por consulta, lo que equivale a unos 25 minutos de envíos. Aumentar `limit` a 1000 permite recuperar aproximadamente 4 horas.
- **Un solo escritor:** SQLite permite un proceso escribiendo a la vez. Si DB Browser u otro programa mantiene la base bloqueada, la ingesta no puede guardar.
- **Distancia no almacenada:** el HC-SR04 no se publica en Adafruit IO, por lo que la base no la registra.
- **Mejoras posibles:** migrar a InfluxDB en una Raspberry Pi para series de tiempo a mayor escala, programar copias de seguridad de `sensores.db`, ejecutar la ingesta como servicio y registrar también la distancia.

---

## 12. Evidencias

| Figura | Descripción | Estado |
|---|---|---|
| 1 | Verificación de Python 3.15.2 en CMD | Incluida |
| 2 | Estructura de `sensores.db` en DB Browser | Incluida |
| 3 | Consola de la ingesta con carga inicial y rondas de registros nuevos | Incluida |
| 4 | Conteo por feed (159 registros cada uno) | Incluida |
| 5 | Vista por envío con las últimas 10 mediciones | Incluida |
| 6 | ESP32 publicando en Thonny | Incluida |
| 7 | Consulta de duplicados (0 filas) | Pendiente |
| 8 | Conteo antes del reinicio | Pendiente |
| 9 | Conteo después del reinicio | Pendiente |
| 10 | Programador de tareas con la ingesta en ejecución | Pendiente |
| 11 | Dashboard de Adafruit IO | Pendiente |
