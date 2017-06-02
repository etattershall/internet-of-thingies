import sys
import time
import select
import paho.mqtt.client as mqtt
try:
    from ..piduino import piduino
except SystemError:
    sys.path.append('../piduino')
    import piduino
    

def on_connect(client, userdata, rc):
    print("Connected with result code " + str(rc))

def on_message(client, userdata, message):
    print('Received message')
    if message.topic.startswith(smart_agent_name + '/public/'):
        # Locate the appropriate edge device
        destination_id = message.topic.split('/')[2]
        for arduino in arduinos:
            if str(arduino.id) == str(destination_id):
                # Relay the message to the arduino
                relay = {
                         'topic': message.topic.split('/')[4],
                         'payload': message.payload
                         }
                # Send the message
                flag = arduino.send(relay)
                if flag:
                    raise flag
                
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
smart_agent_name = 'TestPi'

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
arduinos = []
for comport in comports:
    arduino = piduino.SerialDevice(comport)

    # Connect
    flag = arduino.connect()
    if flag:
        raise flag
    else:
        arduinos.append(arduino)
# Give the arduinos a chance to connect
time.sleep(4)

# Initiate the handshakes
for arduino in arduinos:
    # Clean out the buffers
    flag = arduino.flush()
    if flag:
        raise flag
    
    # Request a handshake
    flag = arduino.handshake_request()
    if flag:
        raise flag

# Wait for a response, then set the names of the arduinos
responded = 0
while responded < len(arduinos):
    for arduino in arduinos:
        if arduino.ready():
            message = arduino.receive_json()
            if message != '':
                if message["topic"] == "handshake":
                    print(message)
                    arduino.name = message["payload"]
                    responded += 1
            
# Request subscriptions to communications to the attached arduinos
for arduino in arduinos:
    client.subscribe(smart_agent_name + '/public/' + str(arduino.name) + '/output/#', qos=1)

# Start a new thread to process network traffic.
client.loop_start()
try:
    # Receive data
    while True:
        # Wait for a device to be ready
            for arduino in arduinos:
                if arduino.ready():
                    message = arduino.receive_json()
                    if message != '':
                        client.publish(smart_agent_name + '/public/' + str(arduino.name) +'/input/' + message["topic"], 
                               message["payload"], qos=1)

except Exception as e:
    raise e
    
finally:
    for arduino in arduinos:
        arduino.shutdown()
    print('Shutdown was successful')
