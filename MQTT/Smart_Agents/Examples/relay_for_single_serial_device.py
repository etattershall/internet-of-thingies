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
            if device.id == destination_id:
                # Locate the appropriate sensor
                print(message.topic.split('/')[4])
                device.update(message.topic.split('/')[4], message.payload)
                
                
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
ready_to_read, ready_to_write, ready_with_errors = select.select(arduinos, [], [])
for ready_arduino in ready_to_read:
    message = ready_arduino.receive_json()
    if message == '':
        pass
    elif message["topic"] == "handshake":
        print(message)
        ready_arduino.name = message["payload"]
            
# Request subscriptions to communications to the attached arduinos
for arduino in arduinos:
    client.subscribe(smart_agent_name + '/public/' + arduino.name + '/output/#', qos=1)

# Start a new thread to process network traffic.
client.loop_start()
try:
    # Receive data
    while True:
        # Wait for a device to be ready
        ready_to_read, ready_to_write, ready_with_errors = select.select(arduinos, [], [])
        for ready_arduino in ready_to_read:
            message = ready_arduino.receive_json()

            if message == '':
                pass
            else:
                # If successful, publish the message
                client.publish(smart_agent_name + '/public/' + str(ready_arduino.name) +'/input/' + message["topic"], 
                               message["payload"], qos=1)

except Exception as e:
    raise e
    
finally:
    for arduino in arduinos:
        arduino.shutdown()
        print('Shutdown was successful')
