import time
import threading
import paho.mqtt.client as mqtt
import piduino


'''
BROKER THREADS:
    The threads below are called to handle the smart agents connections with the 
    cloud
'''
def on_connect(client, userdata, rc):
    # Thread is called when a connection to the MQTT broker is attempted
    print("Connected with result code " + str(rc))
    if rc == 0:
        client.publish(agent_name + '/private/status', "C" + str(int(time.time())), qos=1) 

def on_message(client, userdata, message):
    # Thread is called when a message is received from the MQTT broker
    print('Received message')
    # If the message is intended for one of our edge devices...
    if message.topic.startswith(agent_name + '/public/'):
        # Locate the appropriate edge device
        destination_id = message.topic.split('/')[2]
        for arduino in devices:
            if str(arduino.name) == str(destination_id):
                # Package the message for the a
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

'''
ARDUINO THREADS:
    The threads below are called to handle the smart agents connections with its
    edge devices
'''
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
            client.publish(agent_name + '/private/log', 'Connected to ' + str(name), qos=1)
            
            # Subscribe to communications from broker concerning this arduino
            client.subscribe(agent_name + '/public/' + str(arduino.name) + '/output/#', qos=1)
            
    arduino.processing = False

def setup(protocol, hostname, agent_name, port):
    '''
    MQTT CLIENT SETUP:
        Set up the client and assign the callback functions. Note that the on_connect
        function does not seem to work on the raspberry pi (either because of 
        python version, paho version or operating system differences *sigh*)
    '''
    if protocol ==  '3.1':
        client = mqtt.Client(protocol=mqtt.MQTTv31)
    else:
        client = mqtt.Client(protocol=mqtt.MQTTv311)
    try:
        client.on_connect = on_connect
    except Exception as e:
        print(e)
    
    client.on_message = on_message
    client.on_publish = on_publish
    
    # Set a LWT that is sent to the broker in the event of unexpected disconnection
    # QoS = 0 because it will be confusing if the message is sent again next time that the smart agent connects
    client.will_set(agent_name + '/private/status', str(int(time.time())) + ' DU', qos=0, retain=True) 
    
    # Attempt to connect to the broker 
    client.connect(hostname, port, 60)
    return client

def mainloop(client, agent_name, devices, threads):
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
    
    # Check that we can still see the broker machine
            
    # Clean out message queue
    # Anything that has been sent should be removed
    # If anything has not been sent in the last 2 seconds...
    
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
                client.publish(agent_name + '/private/log', 'Disconnected from ' + str(arduino.name), qos=1)
                
                # Unsubscribe from communications concerning that arduino
                client.unsubscribe(agent_name + '/public/' + str(arduino.name) + '/output/#')
                # Flag the arduino as disconnected
                arduino.error = True    
                
            if waiting:
                flag, message = arduino.receive_json()
                if flag:
                    print(flag)
                else:

                    if message != '':
                        topic = agent_name + '/public/' + str(arduino.name) +'/input/' + message["topic"]
                        payload = str(int(time.time())) + ' ' + str(message["payload"])

                        # The mqtt code takes care of buffering messages automatically
                        client.publish(topic, payload, qos=1)
                        
                        # Remember the topic being published by the arduino
                        arduino.topics.add(message["topic"])
    
            
    # Clean disconnected arduinos out of the list
    devices = [d for d in devices if not d.error]
    return client, devices, threads 

def clean_up(client, agent_name, devices):
    client.publish(agent_name + '/private/status', str(int(time.time())) + ' DG ', qos=1) 
    client.disconnect()
    for arduino in devices:
        try:
            arduino.shutdown()
        except:
            pass
    print('Shutdown was successful')
    
    
if __name__ == "__main__":
    '''
    CONSTANTS:
        These values need to be set before use
    '''
    hostname = "vm219.nubes.stfc.ac.uk"
    port = 1883
    agent_name = 'Coffee_Room'

    # If we are serving MQTT on the SCD cloud on Ubuntu 14.04, we are constrained 
    # to using this older protocol
    protocol = '3.1'

    devices = []
    threads = []

    client = setup(protocol, hostname, agent_name, port)
    client.loop_start()
    try:
        while True:
            client, devices, threads = mainloop(client, agent_name, devices, threads)
    except Exception as e:
        raise e
        
    finally:
        clean_up(client, agent_name, devices)
