import sys
import time
import threading
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
        for arduino in devices:
            if str(arduino.name) == str(destination_id):
                # Relay the message to the arduino
                relay = {
                         'topic': message.topic.split('/')[4],
                         'payload': message.payload.decode()
                         }
                # Send the message
                if arduino.connected and arduino.verified:
                    flag = arduino.send(relay)
                    if flag:
                        raise flag


def on_publish(client, userdata, mid):
    pass

def on_subscribe(client, userdata, mid, granted_qos):
    print("Successfully subscribed to relevant communications")

def on_disconnect(client, userdata, rc):
    print('Successfully disconnected from broker')

def handshake_protocol(serial_device, timeout=5):
    '''
    Given a device, request a handshake. If handshake is completed,
    return the name of the device. Otherwise return None.
    '''
    # Clean out the buffers
    flag = serial_device.flush()
    if flag:
        raise flag
    
    # Request a handshake
    print('Sending handshake request')
    flag = serial_device.handshake_request()
    if flag:
        raise flag
        
    t0 = time.time()
    # Wait for a response
    while time.time() - t0 < timeout:
        if serial_device.ready():
            flag, message = serial_device.receive_json()
            if type(flag) == piduino.NotConnectedError:
                # The device has been disconnected!
                return None
            else:
                if message != '':
                    if message["topic"] == "handshake":
                        return message["payload"]
    return None
            
def connection_thread(arduino):
    # handles the connection
    arduino.processing = True
    # Connect
    flag = arduino.connect()
    if flag:
        arduino.error = True
        print(flag)  
    else:
        
        # Wait (delay is needed before using the serial port)
        time.sleep(4)
    
        # Handshake
        name = handshake_protocol(arduino)
        if name == None:
            arduino.error = True
            print('Handshake failed!')
        else:
            print('Handshake was successful: we are now connected to device ' + str(name))
            arduino.name = name
            arduino.verified = True
            
            # Inform the broker of this new arduino
            client.publish(smart_agent_name + '/private/log', 'Connected to ' + str(name), qos=1)
            
            # Subscribe to communications from broker concerning this arduino
            client.subscribe(smart_agent_name + '/public/' + str(arduino.name) + '/output/#', qos=1)
            
    arduino.processing = False
            
    
broker_name = "vm219.nubes.stfc.ac.uk"
broker_port = 1883
smart_agent_name = 'TestPi'
previously_connected = []

# If we are serving MQTT on the SCD cloud on Ubuntu 14.04, we are constrained 
# to using this older protocol
protocol = mqtt.MQTTv31

client = mqtt.Client(protocol=protocol)
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish

# Set a LWT that is sent to the broker in the event of unexpected disconnection
client.will_set(smart_agent_name + '/private/log', 'Unexpected disconnection!', 1, False)

# Connect to the broker
client.connect(broker_name, broker_port, 60)


devices = []
threads = []
client.loop_start()
try:
    while True:
        # Make connections to arduinos
        # Check for serial connections to suitable devices
        comports = piduino.comport_scan('Arduino')
        
        
        for comport in comports:
            # Check if we are already connected to this device
            if comport not in [d.comport for d in devices]:
                # If not, create a new device manager
                arduino = piduino.SerialDevice(comport)
                devices.append(arduino)
                
                # Spawn a new thread to handle the process of connection
                t = threading.Thread(name=comport, target=connection_thread, args=(arduino,))
                threads.append(t)
                t.start()
            
        # Receive data
        for arduino in devices:
            if arduino.connected and arduino.verified:
                flag, waiting = arduino.ready()
                
                if type(flag) == piduino.NotConnectedError:
                    # The device has been disconnected! Remove it from our list of verified devices
                    try:
                        arduino.shutdown()
                    except:
                        pass
                    
                    print('Unable to read from arduino at ' + str(arduino.name))
                    # Inform the broker that the arduino is unreachable
                    client.publish(smart_agent_name + '/private/log', 'Disconnected from ' + str(arduino.name), qos=1)
                    # Unsubscribe from communications concerning that arduino
                    client.unsubscribe(smart_agent_name + '/public/' + str(arduino.name) + '/output/#')
                    # Flag the arduino as disconnected
                    arduino.error = True    
                    
                if waiting:
                    flag, message = arduino.receive_json()
                    if flag:
                        print(flag)
                    else:

                        if message != '':
                            client.publish(smart_agent_name + '/public/' + str(arduino.name) +'/input/' + message["topic"], 
                                   message["payload"], qos=1)
                            
                            # Remember the topic being published by the arduino
                            arduino.topics.add(message["topic"])
        
        # Clean disconnected arduinos out of the list
        devices = [d for d in devices if not d.error]
        

                            
        

except Exception as e:
    raise e
    
finally:
    #client.disconnect()

    for arduino in devices:
        try:
            arduino.shutdown()
        except:
            pass
    print('Shutdown was successful')
