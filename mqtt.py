from mqtt_as import MQTTClient, config
import uasyncio as asyncio

# Configuración del broker MQTT
config['server'] = '192.168.100.9'  # Broker público
config['port'] = 1883  # Puerto para conexiones SSL
config['ssl'] = False  # Habilitar SSL
config['ssid'] = 'IGNACIO-5G'  # Nombre de tu red WiFi
config['wifi_pw'] = 'pepito28'  # Contraseña de tu red WiFi

# Función para manejar la conexión al broker
async def on_connect(client):
    await client.subscribe('casa/habitacion/temperatura', 1)  # Suscribirse al tópico 'nachito'
    print("Suscrito al tópico 'casa/habitacion/temperatura'")

# Función para manejar el estado del WiFi
async def on_wifi(state):
    print('WiFi', 'conectado' if state else 'desconectado')

# Asignar las funciones al diccionario de configuración
config['connect_coro'] = on_connect
config['wifi_coro'] = on_wifi

# Crear cliente MQTT
client = MQTTClient(config)

# Función para conectar al broker
async def connect_mqtt():
    await client.connect()
    print("Conectado al broker MQTT")

# Función para publicar mensajes
async def publish_message(topic, message, qos=1):
    await client.publish(topic, message, qos)
    print(f"Mensaje publicado en {topic}: {message}")

# Función para mantener la conexión activa
async def mqtt_loop():
    while True:
        await asyncio.sleep(1)  # Mantener el bucle activo