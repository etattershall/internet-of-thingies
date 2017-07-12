import time
import threading
import logging
import paho.mqtt.client as Mqtt
import piduino
import tkinter
from sys import version_info

assert version_info >= (3, 0)

HOSTNAME = "vm219.nubes.stfc.ac.uk"
PORT = 1883
AGENTNAME = 'Emma_PC'

TOPIC_ROOT = AGENTNAME
TOPIC_STATUS = AGENTNAME + "/private/status"
TOPIC_EDGE =  AGENTNAME + "/private/edge/"
TOPIC_DISCOVERY = TOPIC_ROOT + "/discover"

STATUS_CONNECTED = "C"
STATUS_DISCONNECTED_GRACE = "DG"
STATUS_DISCONNECTED_UNGRACE = "DU"

logging.basicConfig(level=logging.INFO)


global SPACING
global BACKGROUND
global FONT

global MODE
global STATE
global messagebox
global statusbox



'''
BROKER THREADS:
    The threads below are called to handle the smart agents connections with the 
    cloud
'''
def handle_connect(mqttClient, userdata, rc):
    """After connection with MQTT broker established, check for errors and
    subscribe to topics."""
    global connected
    if rc != 0:
        logging.error("Connection returned result: " + Mqtt.connack_string(rc))
        connected = False
    else:
        logging.info("Connection to MQTT broker succeeded.")
        mqttClient.publish(TOPIC_STATUS, STATUS_CONNECTED + str(int(time.time())), qos=1)
        connected = True

def handle_message(mqttClient, userdata, message):
    global messagebox
    # Thread is called when a message is received from the MQTT broker
    # If the message is intended for one of our edge devices...
    if message.topic.startswith(AGENTNAME + '/public/'):
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
                        
    # Deal with gui actions
    if MODE == 'GUI':
        messagebox.append(message.topic + ': ' + message.payload.decode())

def handle_publish(mqttClient, userdata, mid):
    """Called when a publish handshake is finished (depending on the qos)"""
    pass


def handle_subscribe(mqttClient, userdata, mid, granted_qos):
    """Called after the MQTT client successfully subscribes to a topic."""
    logging.info("Subscribed to a topic with mid: {}".format(mid))

def handle_disconnect(mqttClient, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    global connected
    connected = False
    if shouldBeConnected:
        logging.error("Disconnected from MQTT ungracefully.")
    else:
        mqttClient.loop_stop()
        logging.info("Disconnected from MQTT gracefully.")

'''
ARDUINO THREADS:
    The threads below are called to handle the smart agents connections with its
    edge devices
'''
def handshake_protocol(device, timeout=5):
    '''
    Given a device, request a handshake. If handshake is completed,
    return the name of the device. Otherwise return None.
    '''
    global statusbox
    # Clean out the buffers
    flag = device.flush()
    if flag:
        raise flag
    
    # Request a handshake
    logging.info('Sending handshake request to new device')
    if MODE == 'GUI':
        statusbox.append('Sending handshake request')
    flag = device.handshake_request()
    if flag:
        raise flag
        
    t0 = time.time()
    # Wait for a response
    while time.time() - t0 < timeout:
        if device.ready():
            flag, message = device.receive_json()
            if type(flag) == piduino.NotConnectedError:
                # The device has been disconnected!
                return None
            else:
                if message != '':
                    if message["topic"] == "handshake":
                        return message["payload"]
    return None
            
def connection_thread(device, client):
    global statusbox
    # handles the connection
    device.processing = True
    # Connect
    flag = device.connect()
    if flag:
        device.error = True
        logging.error(flag) 
    else:
        
        # Wait (delay is needed before using the serial port)
        time.sleep(4)
    
        # Handshake
        name = handshake_protocol(device)
        if name == None:
            device.error = True
            logging.error('Handshake failed!')
        else:
            logging.info('Handshake was successful: we are now connected to device ' + str(name))
            if MODE == 'GUI':
                statusbox.append('Handshake was successful: we are now connected to device ' + str(name))
            device.name = name
            device.verified = True
            
            # Inform the broker of this new arduino
            client.publish(AGENTNAME + '/private/log', 'Connected to ' + str(name), qos=1)
            
            # Subscribe to communications from broker concerning this arduino
            client.subscribe(AGENTNAME + '/public/' + str(device.name) + '/output/#', qos=1)
            
            if MODE == 'GUI':
                client.subscribe(AGENTNAME + '/#', qos=1)
    device.processing = False

'''
THREAD MANAGEMENT
'''
def setup():
    """Sets up an mqtt client, registers the handlers and starts a
    threaded loop."""
    global connectedEdgeDevices
    global shouldBeConnected
    global messagesInTransit
    global runningThreads
    global connected
    # Assume connected unless proved otherwise
    connected = True
    connectedEdgeDevices = []
    shouldBeConnected = False
    messagesInTransit = dict()
    runningThreads = []

    if PROTOCOL ==  '3.1':
        client = Mqtt.Client(protocol=Mqtt.MQTTv31)
    else:
        client = Mqtt.Client(protocol=Mqtt.MQTTv311)
    try:
        client.on_connect = handle_connect
    except Exception as e:
        print(e)
    
    client.on_message = handle_message
    client.on_publish = handle_publish
    client.on_subscribe = handle_subscribe
    client.on_disconnect = handle_disconnect
    # Set a LWT that is sent to the broker in the event of unexpected disconnection
    # QoS = 0 because it will be confusing if the message is sent again next time that the smart agent connects
    client.will_set(TOPIC_STATUS, str(int(time.time())) + ' DU', qos=0, retain=True) 
    
    # Attempt to connect to the broker 
    logging.info("Connecting to MQTT broker...")
    client.connect(HOSTNAME, PORT, 60)
    shouldBeConnected = True
    return client

def mainloop(client):
    global connectedEdgeDevices
    global runningThreads
    global connected
    global shouldBeConnected
    # Fix connection
    if not connected and shouldBeConnected:
        connected = True
        logging.info("Reconnecting to MQTT broker...")
        client.connect(HOSTNAME, PORT, 60)
    
    # Make connections to arduinos
    # Check for serial connections to suitable devices
    comports = piduino.comport_scan('Arduino')
    
    
    for comport in comports:
        # Check if we are already connected to this device
        if comport not in [d.comport for d in connectedEdgeDevices]:
            # If not, create a new device manager
            device = piduino.SerialDevice(comport)
            connectedEdgeDevices.append(device)
            
            # Spawn a new thread to handle the process of connection
            t = threading.Thread(name=comport, target=connection_thread, args=(device, client,))
            runningThreads.append(t)
            t.start()
    
    # Check that we can still see the broker machine
            
    # Clean out message queue
    # Anything that has been sent should be removed
    # If anything has not been sent in the last 2 seconds...
    
    # Receive data
    for device in connectedEdgeDevices:
        if device.connected and device.verified:
            flag, waiting = device.ready()
            
            if type(flag) == piduino.NotConnectedError:
                # The device has been disconnected! Remove it from our list of verified devices
                try:
                    device.shutdown()
                except:
                    pass
                
                logging.warning('Unable to read from arduino at ' + str(device.name))
                # Inform the broker that the arduino is unreachable
                client.publish(TOPIC_EDGE + str(device.name), str(int(time.time())) + ' ' + 
                               str(device.name) + ' ' + STATUS_DISCONNECTED_UNGRACE, qos=1)
                
                # Unsubscribe from communications concerning that arduino
                client.unsubscribe(AGENTNAME + '/public/' + str(device.name) + '/output/#')
                # Flag the arduino as disconnected
                device.error = True    
                
            if waiting:
                flag, message = device.receive_json()
                if flag:
                    print(flag)
                    logging.error(flag)
                else:
                    if message != '':
                        topic = AGENTNAME + '/public/' + str(device.name) +'/input/' + message["topic"]
                        payload = str(int(time.time())) + ' ' + str(message["payload"])

                        # The mqtt code takes care of buffering messages automatically
                        client.publish(topic, payload, qos=1)
                        
                        # Remember the topic being published by the arduino
                        device.topics.add(message["topic"])
    
            
    # Clean disconnected arduinos out of the list
    connectedEdgeDevices = [d for d in connectedEdgeDevices if not d.error]
    return client

def clean_up(client):
    global connectedEdgeDevices
    global shouldBeConnected
    
    for device in connectedEdgeDevices:
        try:
            device.shutdown()
            logging.info('Disconnected from device ' + str(device.name))
            client.publish(TOPIC_EDGE + str(device.name), str(int(time.time())) + ' ' + STATUS_DISCONNECTED_GRACE, qos=1)
        except:
            logging.warning('Encountered problems when disconnecting from device ' + str(device.name))
            client.publish(TOPIC_EDGE + str(device.name), str(int(time.time())) + ' ' + STATUS_DISCONNECTED_UNGRACE, qos=1)
            pass
        
    client.publish(TOPIC_STATUS, str(int(time.time())) + ' ' + STATUS_DISCONNECTED_GRACE, qos=1) 
    shouldBeConnected = False
    client.disconnect()
    logging.info('Shutdown was successful')

'''
GUI WIDGETS AND CALLBACKS
'''
class ScrollTextFrame():
    def __init__(self, parent, padding, labeltext, height, width):
        
        self.frame = tkinter.Frame(parent, borderwidth=1, bg=BACKGROUND,)
        self.frame.pack(side=tkinter.LEFT, padx=padding, pady=padding)

        self.label = tkinter.Label(self.frame, justify=tkinter.LEFT, padx=SPACING,
                                   bg=BACKGROUND,
                                   font=(FONT, 12),
                                    text=labeltext).pack()
        self.scrollbar = tkinter.Scrollbar(self.frame)
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.textbox = tkinter.Text(self.frame, height=height, width=width)
        self.textbox.pack()
        
        # attach listbox to scrollbar
        self.textbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.textbox.yview)
    
class InputBox():
    '''
    Creates an input box with label
    '''
    def __init__(self, parent, labeltext, default=''):
        self.label = tkinter.Label(parent, justify=tkinter.LEFT,
                                   bg=BACKGROUND,
                                  font=(FONT, 12),
                                  text=labeltext).pack()
        self.inputbox = tkinter.Entry(parent, width=30)
        self.inputbox.insert(0, default)
        self.inputbox.pack()

def start_callback():
    '''
    Check input
    '''
    global HOSTNAME
    global AGENTNAME
    global PORT
    global PROTOCOL
    global STATE
    HOSTNAME = cloud_name_choice.inputbox.get()
    if HOSTNAME == '':
        status_frame.textbox.insert(tkinter.END, 'Please fill in a cloud name\n')
        status_frame.textbox.see(tkinter.END)
        return None
    AGENTNAME = user_name_choice.inputbox.get()
    if AGENTNAME == '':
        status_frame.textbox.insert(tkinter.END, 'Please fill in a user name\n')
        status_frame.textbox.see(tkinter.END)
        return None
    PORT = port_choice.inputbox.get()
    if PORT == '':
        status_frame.textbox.insert(tkinter.END, 'No port chosen: using default (1883)\n')
        PORT = 1883
    else:
        try:
            PORT = int(PORT)
        except:
            status_frame.textbox.insert(tkinter.END, 'Need an integer port: using default (1883)\n')
            PORT = 1883

    PROTOCOL = '3.1'
    STATE = 'starting'
    
    print('START')
    
def stop_callback():
    global STATE
    clean_up(client)
    STATE = 'waiting'
    print('STOP')

    
    
if __name__ == "__main__":

    MODE = 'NoGUI'
    STATE = 'waiting'
    
    if MODE != 'GUI':
        HOSTNAME = "vm219.nubes.stfc.ac.uk"
        PORT = 1883
        AGENTNAME = 'Emma_PC'
    
        # If we are serving MQTT on the SCD cloud on Ubuntu 14.04, we are constrained 
        # to using this older protocol
        PROTOCOL = '3.1'
    
        client = setup()
        client.loop_start()
        try:
            while True:
                client = mainloop(client)
        except Exception as e:
            raise e
            
        finally:
            clean_up(client)
            
    else:
        
        SPACING = 2
        BACKGROUND = 'LightSteelBlue1'
        FONT = 'Helvetica'
        
        root = tkinter.Tk("Internet of thingies")
        root.configure(bg=BACKGROUND)
        
        title_frame = tkinter.Frame(root, borderwidth=1)
        title_frame.configure(bg=BACKGROUND)
        title_frame.pack(padx=SPACING, pady=SPACING)
        
        title_label = tkinter.Label(title_frame, justify=tkinter.LEFT, padx=SPACING,
                                    bg=BACKGROUND,
                                    font=(FONT, 24),
                                    text="Internet of Thingies").pack()
        
        
        
        centre_frame = tkinter.Frame(root, borderwidth=1)
        centre_frame.configure(bg=BACKGROUND)
        centre_frame.pack(padx=SPACING, pady=SPACING)
        
        '''
        CONFIGURATION 
        '''
        
        left_centre_frame = tkinter.Frame(centre_frame, bg=BACKGROUND, borderwidth=1)
        
        
        
        cloud_name_choice = InputBox(left_centre_frame, "Cloud network address", default="vm219.nubes.stfc.ac.uk")
        user_name_choice = InputBox(left_centre_frame, "This computer's name", default="test")
        port_choice = InputBox(left_centre_frame, "Cloud network port (advanced)", default='1883')
        
        status_frame = ScrollTextFrame(left_centre_frame, SPACING, "Status", 12, 30)
        left_centre_frame.pack(side=tkinter.LEFT, padx=SPACING, pady=SPACING)
        
        '''
        OUTPUT DATA
        '''
        messages_frame = ScrollTextFrame(centre_frame, SPACING, "Messages sent/received", 20, 60)
        
        '''
        NETWORK VIEW
        '''
        network_data_frame = ScrollTextFrame(centre_frame, SPACING, "Network", 20, 30)
        
        
        '''
        CONTROL BUTTONS
        '''
        bottom_frame = tkinter.Frame(root, borderwidth=1)
        bottom_frame.configure(bg=BACKGROUND)
        bottom_frame.pack(padx=SPACING, pady=SPACING)
        
        stop_button = tkinter.Button(bottom_frame, text="STOP", command=stop_callback)
        stop_button.pack(side=tkinter.RIGHT, padx=SPACING, pady=SPACING)
        
        # The start button kickstarts this whole thing
        start_button = tkinter.Button(bottom_frame, text="START", command=start_callback)
        start_button.pack(side=tkinter.RIGHT)
        
        
        try:
            while True:
                
                if STATE == 'starting':
                    status_frame.textbox.insert(tkinter.END, 'Starting\n')
                    devices = []
                    threads = []
                    messagebox = []
                    statusbox = []
                    try:
                        client = setup()
                        client.loop_start()
                        STATE = 'running'
                    except Exception as e:
                        status_frame.textbox.insert(tkinter.END, e + '\n')
                        status_frame.textbox.see(tkinter.END)
                        STATE = 'waiting'
                    
                     
                elif STATE == 'running':
                    try:
                        for message in messagebox:
                            messages_frame.textbox.insert(tkinter.END, message+'\n')
                            messages_frame.textbox.see(tkinter.END)
                            messagebox = []
                        for status in statusbox:
                            status_frame.textbox.insert(tkinter.END, status+'\n')
                            status_frame.textbox.see(tkinter.END)
                            statusbox = []

                        client, devices, threads = mainloop(client, devices, threads)
                        status_frame.textbox.see(tkinter.END)
                    except Exception as e:
                        raise e
            
                root.update()
        except Exception as e:
            raise e
            
        finally:
            clean_up(client, devices)



                
