	
# Sistema de Monitoreo de Luminosidad en Aula con ESP32

## 1. Descripción del Proyecto
Este proyecto implementa una solución de monitoreo ambiental para aulas de clase utilizando un microcontrolador ESP32 y MicroPython. El sistema mide los niveles de luz mediante una fotorresistencia (LDR) conectada a un conversor analógico-digital (ADC) y publica las lecturas periódicamente a Adafruit IO mediante el protocolo MQTT. Cuando la iluminación desciende por debajo del umbral de confort visual (1000 lux), el servicio IFTTT detecta la condición y dispara una notificación push automática al teléfono del coordinador académico.

## 2. Diagrama y Conexiones de Hardware
* **Microcontrolador:** ESP32 NodeMCU
* **Sensor de Luminosidad:** Módulo LDR conectado al pin analógico **GPIO 34** (o GPIO 33)
* **Alimentación:** 3.3V y GND desde la placa ESP32

## 3. Flujo de Datos
El flujo de supervisión y alerta opera en la siguiente secuencia:
1. **Sensor LDR:** Captura la variación de resistencia según la luz del aula.
2. **ESP32 (MicroPython):** Convierte la señal analógica, procesa el valor y publica el dato vía MQTT cada 12 segundos hacia Adafruit IO.
3. **Adafruit IO:** Almacena el dato histórico en el feed `luminosidad` y actualiza el dashboard en tiempo real.
4. **IFTTT:** Monitorea el feed (`luminosidad < 1000`) mediante un disparador de sondeo.
5. **Smartphone:** Recibe la notificación push de alerta en la aplicación de IFTTT.

## 4. Evidencias del Funcionamiento
* Configuración del Applet en IFTTT: `evidencias/applet_ifttt.png`
* Notificación push recibida en el móvil: `evidencias/notificacion_push.png`
* Gráfica histórica de caídas de luz: `evidencias/grafico_historico.png`
* Panel de control completo: `evidencias/dashboard_adafruit.png`

## 5. Conclusiones sobre la Automatización en IoT
La integración entre microcontroladores de bajo costo y plataformas en la nube permite implementar sistemas de supervisión eficientes sin requerir servidores locales dedicados. Aunque el plan gratuito de IFTTT introduce latencia por sondeo horario, el desacoplamiento mediante MQTT y servicios de eventos facilita la automatización de alertas críticas en entornos educativos e industriales.