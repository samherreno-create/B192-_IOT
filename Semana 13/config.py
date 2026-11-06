WIFI_SSID = "JULIAN"
WIFI_PASSWORD = "1098817824camilo"
THINGSPEAK_API_KEY = "N9FFKWUTWOOKPKIF"
INTERVALO_ENVIO_S = 15
TELEGRAM_BOT_TOKEN = "8823613804:AAFbbrjrGBRD19QkaCwz3N9Yi-HBJJgFTbk"
TELEGRAM_CHAT_ID = "6106044845"

# Configuración MQTT (Semana 10)
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "ESP32_GutierrezHerreno_UTS"
MQTT_TOPIC_TEMP = "aula/uts/gutierrez_herreno/temperatura"
MQTT_TOPIC_HUM = "aula/uts/gutierrez_herreno/humedad"
MQTT_TOPIC_LUZ = "aula/uts/gutierrez_herreno/luminosidad"
MQTT_TOPIC_ESTADO = "aula/uts/gutierrez_herreno/estado"

# Configuración Adafruit IO (Semana 12)
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USERNAME = "JulianGtzx"
AIO_KEY = "aio_OJHw44QKvCTKDnqEVvgusG8Kfbtg"
AIO_CLIENT_ID = "ESP32_GutierrezHerreno_AIO"
AIO_FEED_TEMP = AIO_USERNAME + "/feeds/temperatura"
AIO_FEED_HUM = AIO_USERNAME + "/feeds/humedad"
AIO_FEED_LUZ = AIO_USERNAME + "/feeds/luminosidad"
AIO_FEED_LED = AIO_USERNAME + "/feeds/led-rojo"
AIO_FEED_BUZZER = AIO_USERNAME + "/feeds/buzzer"