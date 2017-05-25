import sys
import time

import paho.mqtt.client as mqtt
try:
    from ..piduino import piduino
except SystemError:
    sys.path.append('../piduino')
    import piduino
    

def on_connect(client, userdata, rc):
    print("Connected with result code " + str(rc))

def on_message(client, userdata, message):
    # Relay the message to the arduino
    if arduino != None:
        relay = {
        'topic': 'led', 
        'payload': message.payload.decode()
        }
        flag = arduino.send(relay)
        if flag:
            raise flag

def on_publish(client, userdata, mid):
    pass

def on_subscribe(client, userdata, mid, granted_qos):
    print("Successfully subscribed to webapp communications")

broker_name = "vm219.nubes.stfc.ac.uk"
broker_port = 1883

# If we are serving MQTT on the SCD cloud on Ubuntu 14.04, we are constrained 
# to using this older protocol
protocol = mqtt.MQTTv31

client = mqtt.Client(protocol=protocol)
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish

# Connect to the broker
client.connect(broker_name, broker_port, 60)

# Check for serial connections to suitable devices
comports = piduino.comport_scan('Arduino')
arduino = piduino.SerialDevice(comports[0])

# Connect
flag = arduino.connect()
if flag:
    raise flag

# Give the arduino a chance to connect
time.sleep(4)

# Request a subscriptrion to test/webapp
client.subscribe('test/webapp/#', qos=1)

# Start a new thread to process network traffic.
client.loop_start()
try:
    # Receive data
    while True:
        # Attempt to receive a single message from the Arduino
        message = arduino.receive_json()
        if message == '':
            pass
        else:
            # If successful, publish the message
            if message["type"] == "pub":
                client.publish('test/arduino/' + message["topic"], message["payload"], qos=1)

except Exception as e:
    raise e
finally:
    arduino.shutdown()
