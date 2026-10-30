# ==========================================
# CONFIGURACIÓN SEGURA DE CREDENCIALES
# ==========================================

# Red WiFi
WIFI_SSID = "TU_WIFI_SSID"
WIFI_PASSWORD = "TU_WIFI_PASSWORD"

# ThingSpeak
THINGSPEAK_API_KEY = "TU_THINGSPEAK_API_KEY"
INTERVALO_ENVIO_S = 20

# Telegram Bot
TELEGRAM_BOT_TOKEN = "TU_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "TU_TELEGRAM_CHAT_ID"

# MQTT Broker Público (Semana 10)
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "ESP32_Proyecto_UTS"
MQTT_TOPIC_TEMP = "aula/uts/proyecto/temperatura"
MQTT_TOPIC_HUM = "aula/uts/proyecto/humedad"
MQTT_TOPIC_LUZ = "aula/uts/proyecto/luminosidad"
MQTT_TOPIC_ESTADO = "aula/uts/proyecto/estado"

# Adafruit IO (Semana 12 - Cloud y Control Bidireccional)
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USERNAME = "TU_USUARIO_ADAFRUIT"
AIO_KEY = "TU_AIO_KEY_SECRETA"
AIO_CLIENT_ID = "ESP32_Proyecto_AIO"
AIO_FEED_TEMP = AIO_USERNAME + "/feeds/temperatura"
AIO_FEED_HUM = AIO_USERNAME + "/feeds/humedad"
AIO_FEED_LUZ = AIO_USERNAME + "/feeds/luminosidad"
AIO_FEED_LED = AIO_USERNAME + "/feeds/led-rojo"
AIO_FEED_BUZZER = AIO_USERNAME + "/feeds/buzzer"