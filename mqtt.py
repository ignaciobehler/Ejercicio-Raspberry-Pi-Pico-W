from mqtt_as import MQTTClient, config
from settings import SSID, password
import uasyncio as asyncio
import json
import machine
from machine import Pin
import dht
import ujson

# Generar ID del dispositivo basado en el identificador único del microcontrolador
id = ""
for b in machine.unique_id():
    id += "{:02X}".format(b)
print(f"ID del dispositivo: {id}")
DEVICE_ID = id

# Archivo de almacenamiento de parámetros
PARAMS_FILE = "params.json"

def load_params():
    try:
        with open(PARAMS_FILE, "r") as f:
            return ujson.load(f)
    except:
        return {"setpoint": 30.0, "periodo": 10, "modo": "automatico", "relé": 0}

def save_params(params):
    try:
        with open(PARAMS_FILE, "w") as f:
            ujson.dump(params, f)
    except:
        print("Error! No se pudo guardar los parámetros")

# Cargar parámetros iniciales
params = load_params()

# Configuración del broker MQTT
config['server'] = 'iotunam.duckdns.org'  # Broker público
config['port'] = 8883  # Puerto para conexiones SSL
config['ssl'] = True  # Habilitar SSL
config['ssid'] = SSID  # Nombre de tu red WiFi
config['wifi_pw'] = password  # Contraseña de tu red WiFi

# Inicializar sensor DHT22 en GPIO específico (ajustar según hardware)
try:
    dht_sensor = dht.DHT22(machine.Pin(15))  # Ajustar al pin correcto
    dht_available = True
except Exception as e:
    print(f"Error al inicializar DHT22: {e}")
    dht_available = False

# Función para manejar la conexión al broker
async def on_connect(client):
    topics = [f"{DEVICE_ID}/setpoint", f"{DEVICE_ID}/periodo", f"{DEVICE_ID}/modo", f"{DEVICE_ID}/relé", f"{DEVICE_ID}/destello"]
    for topic in topics:
        await client.subscribe(topic, 1)
    print(f"Suscrito a los tópicos de {DEVICE_ID}")


# Función para manejar los mensajes recibidos
async def on_message(topic, msg, retained):
    global params
    topic_str = topic.decode("utf-8")
    msg_str = msg.decode("utf-8")
    
    print(f"Mensaje recibido en {topic_str}: {msg_str}")  # Agregar esta línea para depuración
    
    if topic_str.endswith("setpoint"):
        params["setpoint"] = float(msg_str)
    elif topic_str.endswith("periodo"):
        params["periodo"] = int(msg_str)
    elif topic_str.endswith("modo"):
        if msg_str == "automatico":
            params["modo"] = "automatico"
        elif msg_str == "manual":
            params["modo"] = "manual"
    elif topic_str.endswith("relé"):
        params["relé"] = int(msg_str)
    
    # Guardar los parámetros actualizados
    save_params(params)
    print(f"Parámetros actualizados: {params}")

# Función para manejar el estado del WiFi
async def on_wifi(state):
    print('WiFi', 'conectado' if state else 'desconectado')

# Asignar funciones a configuración MQTT
config['connect_coro'] = on_connect
config['wifi_coro'] = on_wifi
config['subs_cb'] = on_message

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

async def publish_status():
    while True:
        try:
            if dht_available:
                dht_sensor.measure()
                temperatura = dht_sensor.temperature()
                humedad = dht_sensor.humidity()
            else:
                raise Exception("Sensor no disponible")
        except Exception as e:
            print(f"Error al leer DHT22: {e}")
            temperatura = 25.0  # Valor por defecto
            humedad = 60.0  # Valor por defecto

        # Controlar el relé según el modo
        controlar_rele(temperatura)

        # Publicar los datos en formato JSON
        data = {
            "temperatura": temperatura,
            "humedad": humedad,
            "setpoint": params["setpoint"],
            "periodo": params["periodo"],
            "modo": params["modo"]
        }
        await publish_message(DEVICE_ID, json.dumps(data), qos=1)
        await asyncio.sleep(params["periodo"])

# Función para mantener la conexión activa
async def mqtt_loop():
    while True:
        await asyncio.sleep(1)


# Inicializar el pin del relé 
rele_pin = Pin(2, Pin.OUT)  # Cambia el número del pin según tu configuración
rele_pin.value(0)  # Inicialmente apagado

# Función para controlar el relé
def controlar_rele(temperatura):
    if params["modo"] == "automatico":  # Modo automático
        if temperatura > params["setpoint"]:
            rele_pin.value(1)  # Encender el relé
        else:
            rele_pin.value(0)  # Apagar el relé
    elif params["modo"] == "manual":  # Modo manual
        rele_pin.value(params["relé"])  # Controlar según el valor recibido por MQTT


async def on_message(topic, msg, retained):
    global params
    topic_str = topic.decode("utf-8")
    msg_str = msg.decode("utf-8")
    
    if topic_str.endswith("setpoint"):
        params["setpoint"] = float(msg_str)
    elif topic_str.endswith("periodo"):
        params["periodo"] = int(msg_str)
    elif topic_str.endswith("modo"):
        if msg_str == "automatico":
            params["modo"] = "automatico"
        elif msg_str == "manual":
            params["modo"] = "manual"
    elif topic_str.endswith("relé"):
        params["relé"] = int(msg_str)
    
    # Guardar los parámetros actualizados
    save_params(params)
    print(f"Parámetros actualizados: {params}")