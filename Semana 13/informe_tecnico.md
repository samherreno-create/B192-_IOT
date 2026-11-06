# Informe Técnico: Monitoreo de Luminosidad y Automatización con ESP32, Adafruit IO e IFTTT

**Estudiante:** Julian Gutierrez
**Curso:** Internet de las Cosas (IoT) - Semana 13

---

## 1. Análisis del Gráfico Histórico de Luminosidad

Durante la ejecución de las pruebas se configuró la tasa de publicación del ESP32 a 12 segundos y se monitorearon las lecturas del sensor LDR a través de un widget *Line Chart* en Adafruit IO.

* **Comportamiento observado:** En condiciones de iluminación ambiental normal, el conversor ADC registró valores estables por encima de 1000 lux (promediando entre 1100 y 1300 unidades analógicas).
* **Simulación de oscuridad:** Al tapar el sensor con un objeto opaco, la curva experimentó caídas abruptas y valles pronunciados, descendiendo hasta niveles cercanos a **206 unidades**, lo cual situó la lectura muy por debajo del umbral de alerta configurado (1000).
* **Consistencia temporal:** Al retirar la cobertura, las lecturas se recuperaron casi de inmediato a sus valores habituales, demostrando la sensibilidad adecuada de la fotorresistencia y la correcta transmisión continua mediante MQTT.

*(Referencia visual: `evidencias/grafico_historico.png` y `evidencias/dashboard_adafruit.png`)*

---

## 2. Preguntas de Reflexión y Análisis Crítico

### Pregunta 1: ¿Por qué es más eficiente usar IFTTT para enviar notificaciones que programar el ESP32 para que envíe un correo directamente por SMTP?
* **Sobrecarga de hardware:** Manejar conexiones SMTP seguras (TLS/SSL) directamente en el microcontrolador consume una cantidad significativa de memoria RAM y potencia de procesamiento del ESP32, lo que puede provocar bloqueos o retardos en la adquisición de datos de los sensores.
* **Mantenimiento y seguridad:** Si se usa SMTP en el código, las credenciales del correo (incluyendo contraseñas de aplicación) quedan almacenadas en texto plano dentro del dispositivo. Utilizar IFTTT traslada la lógica de integración a la nube, desacopla las responsabilidades y facilita cambiar el canal de alerta (push, SMS, Telegram) sin tener que reprogramar el hardware.

### Pregunta 2: ¿Qué limitaciones tiene el plan gratuito de Adafruit IO y cómo impactan en un proyecto de monitoreo en tiempo real?
* **Tasa de limitación de datos (Data Rate):** El plan gratuito restringe el envío a un máximo de 30 a 60 puntos de datos por minuto. Enviar lecturas con frecuencias menores a 2 segundos satura la cola MQTT (*throttling*) y provoca el descarte de paquetes.
* **Retención de historial:** El historial de datos se almacena únicamente durante 30 días, lo que impide realizar análisis estacionales a largo plazo sin un sistema externo de base de datos.
* **Feeds limitados:** Solo permite la creación de un número acotado de feeds y dashboards concurrentes, limitando el escalado para plantas o redes amplias de sensores.

### Pregunta 3: ¿Qué ventajas tiene desacoplar la lógica de alerta (en la nube con IFTTT) en lugar de programarla dentro del ESP32?
* **Flexibilidad operativa:** El umbral de activación (ej. 1000 lux) o las acciones resultantes pueden modificarse directamente desde la interfaz web de IFTTT sin necesidad de conectar el ESP32 a la PC ni compilar/flashear código nuevo.
* **Escalabilidad y múltiples receptores:** Un único feed publicado en la nube puede desencadenar múltiples acciones independientes (notificar a varios coordinadores, registrar eventos en una hoja de Google Sheets, activar relés inteligentes) sin aumentar el consumo de batería o ancho de banda del ESP32.

### Pregunta 4: En una aplicación industrial crítica, ¿sería adecuado usar IFTTT gratuito? ¿Qué alternativa profesional propondría?
* **Inadecuación de IFTTT gratuito:** No es adecuado para entornos industriales críticos debido a su modelo de ejecución basado en sondeo (*polling*) para muchas integraciones, el cual puede presentar demoras de hasta 15 a 60 minutos en disparar la acción, careciendo de garantías de Acuerdo de Nivel de Servicio (SLA) o confirmación de entrega en tiempo real.
* **Alternativas profesionales:**
  1. **Node-RED / EMQX auto-alojado:** Implementar un servidor MQTT local o en nube privada con Node-RED, permitiendo evaluar reglas con latencias de milisegundos.
  2. **Plataformas IoT industriales (AWS IoT Core / Azure IoT Hub):** Servicios diseñados para telemetría industrial que integran AWS SNS o Azure Logic Apps, garantizando entrega push instantánea, alta disponibilidad, cifrado de extremo a extremo y tolerancia a fallos.