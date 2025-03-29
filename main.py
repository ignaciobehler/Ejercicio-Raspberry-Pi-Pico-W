from wlan import connect_wifi
import uasyncio as asyncio
from mqtt import connect_mqtt, publish_message, mqtt_loop

async def main():
    connect_wifi()  # Conectar a la red WiFi
    await connect_mqtt()  # Conectar al broker MQTT

    # Publicar mensajes periódicamente
    n = 0
    while True:
        mensaje = f"Contador: {n}"
        await publish_message('casa/habitacion/temperatura', mensaje, qos=1)  # Publicar en el tópico 'result'
        n += 1
        await asyncio.sleep(10)  # Esperar 10 segundos

# Ejecutar el programa
asyncio.run(main())