# Sistema de Monitoreo de Luminosidad y Ambiente en Aula con ESP32

## 1. Descripción del proyecto
Solución de monitoreo ambiental para aulas con un ESP32 y MicroPython. El sistema mide temperatura y humedad (DHT11) y luminosidad (LDR), publica las lecturas en Adafruit IO cada 15 segundos y, en la Semana 14, guarda esos datos de forma persistente en una base SQLite en un PC mediante un script de ingesta en Python.

Cuando la iluminación baja de 1000 lux, IFTTT envía una notificación push al coordinador académico.

## 2. Hardware
* **Microcontrolador:** ESP32 NodeMCU con MicroPython
* **DHT11 (temperatura y humedad):** GPIO 13
* **LDR (luminosidad):** GPIO 33
* **HC-SR04 (distancia):** TRIG en GPIO 25, ECHO en GPIO 26
* **Actuadores:** LEDs en GPIO 27, 32, 18, 15 y 4; buzzer PWM en GPIO 14
* **Alimentación:** 3.3 V y GND desde la placa ESP32

## 3. Flujo de datos
1. **Sensores:** el DHT11 y el LDR se leen cada 2 segundos.
2. **ESP32 (`main.py`):** cada 15 segundos publica temperatura, humedad y luminosidad en los feeds de Adafruit IO (`temperatura`, `humedad`, `luminosidad`). También envía a ThingSpeak, MQTT y Telegram.
3. **Adafruit IO:** muestra los datos en el dashboard `monitoreo-aula` y conserva el historial 30 días en el plan gratuito.
4. **IFTTT:** monitorea el feed `luminosidad` y envía la alerta cuando el valor es menor que 1000.
5. **Smartphone:** recibe la notificación push.
6. **Ingesta local (`ingesta.py`):** cada 30 segundos consulta la API REST de Adafruit IO y guarda en SQLite solo los datos nuevos.
7. **Base de datos (`sensores.db`):** conserva el historial de forma permanente, más allá de los 30 días de Adafruit IO.

## 4. Almacenamiento avanzado (Semana 14)
* **Base de datos:** SQLite, archivo `C:\proyecto\datos\sensores.db`, tabla `lecturas`.
* **Script:** `ingesta.py`, configurado con variables de entorno desde `run.bat`.
* **Prevención de duplicados:** la columna `aio_id` es `UNIQUE` y el script usa `INSERT OR IGNORE`.
* **Consultas de verificación:** `consultas.sql`.

Esquema de la tabla:

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER (PK) | Identificador local |
| `feed` | TEXT | temperatura, humedad o luminosidad |
| `aio_id` | TEXT UNIQUE | Identificador del dato en Adafruit IO |
| `valor` | TEXT | Valor original |
| `valor_num` | REAL | Valor numérico (NULL si no es número) |
| `creado_en` | TEXT | Marca de tiempo UTC de Adafruit IO |
| `insertado_en` | TEXT | Marca de tiempo UTC del guardado |

## 5. Estructura del repositorio
```
proyecto/
├── main.py                              # Código del ESP32 (MicroPython)
├── config.py                            # Configuración del ESP32 (no subir credenciales reales)
├── ingesta.py                           # Ingesta Adafruit IO -> SQLite
├── run.bat.ejemplo                      # Plantilla de run.bat (sin claves)
├── consultas.sql                        # Consultas de verificación
├── informe_tecnico.md                   # Informe de la Semana 13
├── Documento_Almacenamiento_Avanzado_Semana14.docx
├── evidencias/                          # Capturas del proyecto
└── datos/
    └── sensores.db                      # Base SQLite (generada por ingesta.py)
```

## 6. Cómo ejecutar la ingesta
1. Instala Python 3.15 con la opción **Add Python to PATH** y ejecuta `py -m pip install requests`.
2. Crea `C:\proyecto\` y copia `ingesta.py` dentro.
3. Copia `run.bat.ejemplo` como `run.bat` y reemplaza `TU_USUARIO_AIO` y `TU_AIO_KEY`.
4. Verifica que las keys de los feeds coincidan con `AIO_FEEDS`.
5. Ejecuta `run.bat`. Deben aparecer líneas como `temperatura: 2 registros nuevos`.

Para que arranque al encender el equipo, crea una tarea en el **Programador de tareas** de Windows con el disparador *Al iniciar el sistema* y la acción de ejecutar `C:\proyecto\run.bat`.

## 7. Verificación de persistencia
1. Abre `datos\sensores.db` en DB Browser for SQLite y ejecuta la consulta 1 de `consultas.sql`. Anota el conteo.
2. Reinicia el equipo.
3. Comprueba que la ingesta arrancó sola desde el Programador de tareas.
4. Ejecuta de nuevo la consulta 1. El conteo debe ser igual o mayor, y el primer dato no debe cambiar.

## 8. Evidencias
* Documento de la actividad: `Documento_Almacenamiento_Avanzado_Semana14.docx`
* Ingesta en ejecución y rondas de registros nuevos.
* Conteo de registros por feed y vista por envío.
* Estructura de la base de datos.
* Captura del ESP32 publicando (Thonny).
* Pendientes: resultado de duplicados, prueba de reinicio y Programador de tareas.

## 9. Conclusiones
La integración de un microcontrolador de bajo costo con una plataforma en la nube permite supervisar el aula sin servidores dedicados. Adafruit IO aporta el dashboard y las alertas, mientras que la ingesta local en SQLite conserva el historial completo y da continuidad a los datos más allá del límite de 30 días del plan gratuito.

## 10. Seguridad
No subas `run.bat`, `config.py` con credenciales reales ni `sensores.db` a repositorios públicos. Si una clave se compartió por error, genérala de nuevo en Adafruit IO.
