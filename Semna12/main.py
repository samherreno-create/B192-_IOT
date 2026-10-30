import dht
import network
import time
from machine import ADC, PWM, Pin, time_pulse_us
from config import (
    WIFI_SSID,
    WIFI_PASSWORD,
    THINGSPEAK_API_KEY,
    INTERVALO_ENVIO_S,
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_CLIENT_ID,
    MQTT_TOPIC_TEMP,
    MQTT_TOPIC_HUM,
    MQTT_TOPIC_LUZ,
    MQTT_TOPIC_ESTADO,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    AIO_SERVER,
    AIO_PORT,
    AIO_USERNAME,
    AIO_KEY,
    AIO_CLIENT_ID,
    AIO_FEED_TEMP,
    AIO_FEED_HUM,
    AIO_FEED_LUZ,
    AIO_FEED_LED,
    AIO_FEED_BUZZER,
)
from umqtt.simple import MQTTClient

try:
  import urequests as requests
except ImportError:
  import requests

# ==========================================
# CONFIGURACIÓN DE PINES
# ==========================================
DHT_PIN = 13
LDR_PIN = 33
TRIG_PIN = 25
ECHO_PIN = 26

LED_ROJO_PIN = 27  # Temp > 28 °C
LED_VERDE1_PIN = 32  # Temp <= 28 °C
LED_AMARILLO_PIN = 18  # Hum < 55 %
LED_VERDE2_PIN = 15  # Hum >= 55 %
LED_BLANCO_PIN = 4  # Oscuridad / LDR bajo
BUZZER_PIN = 14  # Alerta Sonora PWM

UMBRAL_LUZ = 1000  # Por debajo de este valor se considera oscuro

sensor_dht = dht.DHT11(Pin(DHT_PIN))
ldr_adc = ADC(Pin(LDR_PIN))
ldr_adc.atten(ADC.ATTN_11DB)

trigger = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)

led_rojo = Pin(LED_ROJO_PIN, Pin.OUT)
led_verde1 = Pin(LED_VERDE1_PIN, Pin.OUT)
led_amarillo = Pin(LED_AMARILLO_PIN, Pin.OUT)
led_verde2 = Pin(LED_VERDE2_PIN, Pin.OUT)
led_blanco = Pin(LED_BLANCO_PIN, Pin.OUT)

buzzer_pwm = PWM(Pin(BUZZER_PIN))
buzzer_pwm.freq(2800)
buzzer_pwm.duty(0)

INTERVALO_MUESTREO = 2000
ultimo_muestreo = time.ticks_ms()

INTERVALO_ENVIO = INTERVALO_ENVIO_S * 1000
ultimo_envio = time.ticks_add(time.ticks_ms(), -INTERVALO_ENVIO)

# Control de anti-spam para Telegram (envía máximo una alerta cada 30 segundos)
ultimo_aviso_telegram = 0

wlan = network.WLAN(network.STA_IF)
mqtt_client = None

# Cliente Adafruit IO (Semana 12)
aio_client = None
ultimo_ping_aio = 0


def conectar_wifi(timeout_s=15):
  wlan.active(False)
  time.sleep_ms(200)
  wlan.active(True)
  time.sleep_ms(200)

  if not wlan.isconnected():
    print(f"[WIFI] Conectando a {WIFI_SSID} ...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    inicio = time.ticks_ms()
    while not wlan.isconnected():
      if time.ticks_diff(time.ticks_ms(), inicio) > timeout_s * 1000:
        print("[WIFI] No se pudo conectar")
        return False
      time.sleep_ms(300)

  ip = wlan.ifconfig()[0]
  mac_raw = wlan.config("mac")
  mac_str = ":".join(["{:02x}".format(b) for b in mac_raw])
  rssi = wlan.status("rssi")
  print(f"\n[WIFI OK] IP: {ip} | MAC: {mac_str} | RSSI: {rssi} dBm")
  return True


def conectar_mqtt():
  global mqtt_client
  try:
    mqtt_client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    mqtt_client.connect()
    print("[MQTT] Conectado exitosamente al broker")
    mqtt_client.publish(MQTT_TOPIC_ESTADO, "online")
    return True
  except Exception as e:
    print("[MQTT] Error al conectar con el broker:", e)
    return False


def enviar_a_thingspeak(datos):
  if not wlan.isconnected():
    return False
  url = (
      "http://api.thingspeak.com/update?api_key={}"
      "&field1={}&field2={}&field3={}&field4={}"
      "&field5={}&field6={}&field7={}&field8={}"
  ).format(
      THINGSPEAK_API_KEY,
      datos["temp"],
      datos["hum"],
      datos["luz"],
      datos["distancia"],
      datos["ventilacion"],
      datos["alerta"],
      datos["iluminacion"],
      datos["ocupado"],
  )
  try:
    r = requests.get(url)
    entrada = r.text.strip()
    r.close()
    if entrada == "0":
      print("[THINGSPEAK] Rechazado (muy seguido)")
      return False
    print(f"[THINGSPEAK] Enviado OK (ID: {entrada})")
    return True
  except Exception as e:
    print("[THINGSPEAK] Error:", e)
    return False


def enviar_a_mqtt(temp, hum, luz):
  global mqtt_client
  try:
    if not mqtt_client:
      if not conectar_mqtt():
        return
    mqtt_client.publish(MQTT_TOPIC_TEMP, str(temp))
    mqtt_client.publish(MQTT_TOPIC_HUM, str(hum))
    mqtt_client.publish(MQTT_TOPIC_LUZ, str(luz))
    print("[MQTT] Datos publicados en tópicos.")
  except Exception as e:
    print("[MQTT] Pérdida de conexión, reintentando...")
    try:
      conectar_mqtt()
    except:
      pass


# ==========================================
# ADAFRUIT IO (SEMANA 12)
# ==========================================
def callback_aio(topic, msg):
  # Comandos desde los interruptores del dashboard
  topic = topic.decode()
  valor = msg.decode().strip().upper()
  encendido = valor in ("1", "ON", "TRUE")
  print("[ADAFRUIT] Comando:", topic, valor)
  if topic == AIO_FEED_LED:
    led_rojo.value(1 if encendido else 0)
  elif topic == AIO_FEED_BUZZER:
    buzzer_pwm.duty(512 if encendido else 0)


def conectar_adafruit():
  global aio_client
  try:
    aio_client = MQTTClient(
        AIO_CLIENT_ID,
        AIO_SERVER,
        port=AIO_PORT,
        user=AIO_USERNAME,
        password=AIO_KEY,
        keepalive=60,
    )
    aio_client.set_callback(callback_aio)
    aio_client.connect()
    aio_client.subscribe(AIO_FEED_LED)
    aio_client.subscribe(AIO_FEED_BUZZER)
    print("[ADAFRUIT] Conectado a Adafruit IO")
    return True
  except Exception as e:
    aio_client = None
    print("[ADAFRUIT] Error al conectar:", e)
    return False


def enviar_a_adafruit(temp, hum, luz):
  global aio_client
  try:
    if not aio_client:
      if not conectar_adafruit():
        return
    aio_client.publish(AIO_FEED_TEMP, str(temp))
    aio_client.publish(AIO_FEED_HUM, str(hum))
    aio_client.publish(AIO_FEED_LUZ, str(luz))
    print("[ADAFRUIT] Datos publicados en feeds.")
  except Exception as e:
    print("[ADAFRUIT] Pérdida de conexión, reintentando...", e)
    aio_client = None


def revisar_adafruit():
  # Recibe comandos del dashboard y mantiene viva la conexión
  global aio_client, ultimo_ping_aio
  if not aio_client:
    return
  try:
    aio_client.check_msg()
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_ping_aio) > 30000:
      aio_client.ping()
      ultimo_ping_aio = ahora
  except Exception as e:
    print("[ADAFRUIT] Conexión perdida:", e)
    aio_client = None


def enviar_telegram(texto):
  if not wlan.isconnected():
    print("[TELEGRAM] Sin WiFi")
    return False
  url = "https://api.telegram.org/bot{}/sendMessage".format(TELEGRAM_BOT_TOKEN)
  data = {"chat_id": TELEGRAM_CHAT_ID, "text": texto}  # sin parse_mode para evitar errores
  try:
    r = requests.post(url, json=data)
    codigo = r.status_code
    r.close()
    if codigo == 200:
      print("[TELEGRAM] Mensaje enviado")
      return True
    print("[TELEGRAM] Error HTTP:", codigo)
    return False
  except Exception as e:
    print("[TELEGRAM] Error:", e)
    return False


def reportar_telegram(temp, hum, luz, distancia, ocupado):
  estado_luz = "Oscuro" if luz < UMBRAL_LUZ else "Iluminado"
  texto = (
      "📊 Reporte del aula\n"
      f"🌡️ Temperatura: {temp} °C\n"
      f"💧 Humedad: {hum} %\n"
      f"💡 Luminosidad: {luz} ({estado_luz})\n"
      f"📏 Distancia: {distancia} cm\n"
      f"👥 Ocupado: {'Sí' if ocupado else 'No'}"
  )
  enviar_telegram(texto)


def enviar_alerta_telegram(temp, hum, distancia, luz):
  global ultimo_aviso_telegram
  tiempo_actual = time.ticks_ms()

  # Evita mandar mensajes seguidos si la condición persiste
  if time.ticks_diff(tiempo_actual, ultimo_aviso_telegram) < 30000:
    return

  if not wlan.isconnected():
    return

  estado_luz = "Oscuro" if luz < UMBRAL_LUZ else "Iluminado"
  texto = (
      "🚨 ¡ALERTA TEMPRANA IOT! 🚨\n"
      "Condición anómala detectada en el aula:\n"
      f"🌡️ Temperatura: {temp} °C\n"
      f"💧 Humedad: {hum} %\n"
      f"💡 Luminosidad: {luz} ({estado_luz})\n"
      f"📏 Distancia: {distancia} cm"
  )
  if enviar_telegram(texto):
    ultimo_aviso_telegram = tiempo_actual


def emitir_tono_alerta():
  buzzer_pwm.duty(512)
  time.sleep_ms(200)
  buzzer_pwm.duty(0)


def medir_distancia():
  trigger.value(0)
  time.sleep_us(2)
  trigger.value(1)
  time.sleep_us(10)
  trigger.value(0)
  duracion = time_pulse_us(echo, 1, 30000)
  if duracion < 0:
    return -1.0
  return round((duracion * 0.0343) / 2, 1)


# ==========================================
# INICIO
# ==========================================
print("=== SISTEMA DE AULA INTELIGENTE (SEMANA 10) ===")
conectar_wifi()
conectar_mqtt()
conectar_adafruit()

# Prueba de conexión con Telegram (puedes quitarla cuando funcione)
enviar_telegram("✅ ESP32 conectado a Telegram")

while True:
  tiempo_actual = time.ticks_ms()
  revisar_adafruit()

  if time.ticks_diff(tiempo_actual, ultimo_muestreo) >= INTERVALO_MUESTREO:
    ultimo_muestreo = tiempo_actual

    try:
      time.sleep_ms(50)
      sensor_dht.measure()
      temp = sensor_dht.temperature()
      hum = sensor_dht.humidity()
      luz = 4095 - ldr_adc.read()
      distancia = medir_distancia()

      print(
          f"\n[DATOS] Temp: {temp}°C | Hum: {hum}% | Luz: {luz} | Dist:"
          f" {distancia}cm"
      )

      # Lógica de Actuadores y Alertas
      if temp > 28:
        led_rojo.value(1)
        led_verde1.value(0)
        enviar_alerta_telegram(temp, hum, distancia, luz)
      else:
        led_rojo.value(0)
        led_verde1.value(1)

      if hum < 55:
        led_amarillo.value(1)
        led_verde2.value(0)
        emitir_tono_alerta()
      else:
        led_amarillo.value(0)
        led_verde2.value(1)

      if luz < UMBRAL_LUZ:
        led_blanco.value(1)
      else:
        led_blanco.value(0)

      ocupado = 1 if 0 < distancia <= 30 else 0

      # Envío Periódico a la Nube (ThingSpeak + MQTT + Adafruit + Telegram)
      if time.ticks_diff(tiempo_actual, ultimo_envio) >= INTERVALO_ENVIO:
        if not wlan.isconnected():
          conectar_wifi(timeout_s=8)

        datos = {
            "temp": temp,
            "hum": hum,
            "luz": luz,
            "distancia": distancia,
            "ventilacion": led_rojo.value(),
            "alerta": led_amarillo.value(),
            "iluminacion": led_blanco.value(),
            "ocupado": ocupado,
        }

        enviar_a_thingspeak(datos)
        enviar_a_mqtt(temp, hum, luz)
        enviar_a_adafruit(temp, hum, luz)
        reportar_telegram(temp, hum, luz, distancia, ocupado)

        ultimo_envio = tiempo_actual

      print("----------------------------------------")

    except OSError:
      print("[ERROR] Fallo al leer sensor DHT11")
      led_rojo.value(0)
      led_amarillo.value(0)
      led_blanco.value(0)
      buzzer_pwm.duty(0)