"""
mF2C-MQTT

This module uses MQTT and JSON based encryption to provide a secure method of
direct messaging in which encryption is handled by a trusted central server.

"""

import logging
import time
import json
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto import Random
import paho.mqtt.client as mqtt

__author__ = "Emma Tattershall & Callum Iddon"
__version__ = "1.3"
__email__ = "etat02@gmail.com, jens.jensen@stfc.ac.uk"
__status__ = "Pre-Alpha"

STATUS_CONNECTED = "C"
STATUS_DISCONNECTED_GRACE = "DG"
STATUS_DISCONNECTED_UNGRACE = "DU"
HUB = 'broker_services'

logging.basicConfig(level=logging.INFO)

def encrypt(payload, destination_public_key):
    # Payload data can be anything; a list, a string, a dictionary...
    payload = json.dumps(payload)
    encrypted_payload = destination_public_key.encrypt(payload.encode(), 32)
    return encrypted_payload[0]
    
def decrypt(encrypted_string):
    plaintext = encrypted_string
    return plaintext

def generate_signature(name, public_key):
    hashed_name = SHA256.new(name.encode()).digest()
    signature = public_key.sign(hashed_name, '')
    return signature
    
def timestamp():
    # Returns a string UNIX time
    return str(int(time.time()))
    
    
"""
Define topic conventions
"""
def topic_public(name):
    return 'mf2c/' + str(name) + '/public'

def topic_protected(name):
    return 'mf2c/' + str(name) + '/protected'
    
def topic_private(name):
    return 'mf2c/' + str(name) + '/private'
    
def topic_pingreq(name):
    return 'mf2c/' + str(name) + '/public/pingreq'

def topic_pingack(name):
    return 'mf2c/' + str(name) + '/public/pingack'

def topic_status():
    return 'mf2c/broker_services/status'

    
def on_connect(mqtt_client, userdata, flags, rc):
    """
    Called when a connect acknowledgement (CONNACK) is received. 
    
    This function sets a global connack flag when broker connection has been
    confirmed.
    """
    global connack
    logging.info("Connected to broker")
    connack = True
    
def on_disconnect(mqtt_client, userdata, rc):
    """
    This function is called when a disconnect packet is sent from this client.
    It is also used if the broker itself disconnects.
    """
    logging.info('Disconnected from broker')
    
def on_publish(mqtt_client, userdata, mid):
    """
    This function is called when a publish acknowledgement (PUBACK) is received. 
    PUBACKs will only be sent if the message has a QoS > 0.
    
    At present, this function is not used.
    """
    pass

def on_message(mqtt_client, userdata, message):
    """
    This function is called when a message is received.
    
    It adds the new messsage to the module-level message buffer. We have chosen 
    to use a buffer rather than dealing with messages in this callback
    function because it means we can provide greater flexibility for users
    """
    global incoming_message_buffer
    incoming_message_buffer.append(message)

class TimeOutError(Exception):
    """
    Timout Error is called when the time taken to receive a connection 
    acknowledgement packet exceeds the user-defined wait time.
    """
    def __init__(self, value):
        self.value = value


class Client():
    """
    Client is the base class for the Smart Agent and Broker Agent classes. It 
    sets class level variables and creates a RSA key pair when it is initialised.
    
    It also contains the methods used in sending a message, and sending and 
    receiving pings since these are the same for any kind of agent.
    """
    def __init__(self, hostname, name, port, protocol):
        # Check input
        assert type(hostname) is str
        assert type(name) is str
        assert type(port) is int
        assert protocol in ['3.1', '3.1.1']

        # Set class level variables
        self.hostname = hostname
        self.name = name
        self.port = port
        # Set protocol. When using older machines in any part of your system,
        # there may only be support for version 3.1
        if protocol == '3.1':
            self.protocol = mqtt.MQTTv31
        elif protocol == '3.1.1':
            self.protocol = mqtt.MQTTv311

        # Set the topics that will be subscribed to
        self.STATUS = topic_status()
        self.BROKER_KEY = topic_key()
        
        # Set a new random generator and create a RSA key pair
        random_generator = Random.new().read
        self.key = RSA.generate(1024, random_generator)
        self.public_key = self.key.publickey()
    
    def package(self, payload_dict, security=0):
        """
        Method adds supplementary information to the supplied payload. At 
        present the added items are:
            - timestamp (UNIX time, str)
            - source (ID of this agent, str)
        """
        payload_dict['timestamp'] = timestamp()
        if 'source' not in payload_dict.keys():
            payload_dict['source'] = self.name

        if security != 0:
            payload_dict['signature'] = generate_signature(self.name, self.public_key)
            
        if security < 2:
            return json.dumps(payload_dict)
        else:
            # Encrypt the payload of the message
            payload_dict['payload'] = encrpyt(payload, broker_public_key)


    def send(self, recipients, payload_dict, security=0, qos=1):
        """
        Method sends a specified jsonic payload to a list of recipients.
        """
        # Check input
        assert type(recipients) == list
        assert len(recipients) > 0
        assert security in [0, 1, 2]
        assert type(payload_dict) == dict

        # Nothing needs to be encrypted if the level of security is set to
        # public
        for recipient in recipients:
            topic = topic_public(recipient)
            # Package the message with a timestamp and information about the
            # source. If security > 0, add a signature. If security==2, encrypt
            # the payload.
            payload_str = self.package(payload_dict, security)
            self.client.publish(topic, payload_str, qos=qos)

    
    def pingack(self, payload_dict):
        """
        Respond to a ping from another device with a ping acknowledgement.
        
        This method is called automatically when a 
        """
        # ping is always public
        try:
            recipient = payload_dict['source']
        except:
            return
        topic = topic_pingack(recipient)
        payload_dict = {
                        'timestamp': timestamp(),
                        'source': self.name
                       }
        self.client.publish(topic, json.dumps(payload_dict), qos=2)
     
    def ping(self, recipients):
        """
        Send a ping request to one or more recipients
        """
        assert type(recipients) == list
        assert len(recipients) > 0
        for recipient in recipients:
            payload_dict = {
                        'timestamp': timestamp(),
                        'source': self.name
                       }
    
            self.client.publish(topic, json.dumps(payload_dict), qos=2)

    def send_handshake(self):
        # Sends a handshake request. Broker
    
        pass
            # Send handshake request
            # Listen for handshake reply
            # Send on mf2c/broker_services/status
            # Listen on normal public inbox.
        
class SmartAgent(Client):
    """
    This class extends the standard Client class.
 
    """
    def __init__(self, hostname, name, port=1883, protocol='3.1'):
        Client.__init__(self, hostname, name, port, protocol)
        # Set the topics that will be subscribed to
        self.PUBLIC = topic_public(self.name)
        self.PROTECTED = topic_protected(self.name)
        self.PRIVATE = topic_private(self.name)
        self.PINGREQ = topic_pingreq(self.name)
        self.PINGACK = topic_pingack(self.name)
        self.HANDSHAKE = topic_handshake(self.name)
        
        self.broker_public_key = None
        
    def setup(self, timeout=20):
        """
        This method sets up the actual MQTT client, assigns all callback 
        functions for event handling and sets a last will and testament (LWT)
        message. 
        
        It then attempts to connect to the broker. The connection call
        is blocking; it continues until a connection acknowlegement message is 
        received from the broker or until the timeout is reached.
        
        After connection has been acheived, it subscribes to the topics:
            mf2c/[name]/public
            mf2c/[name]/protected
            mf2c/[name]/private
            mf2c/[name]/public/pinreq
            mf2c/[name]/public/pingack
            
        If another device wants to contact this smart agent, it must publish to
        one of these topics. 
        
        Finally, this method starts the MQTT loop running on a separate thread.
        This loop thread handles publishing and receiving messages, and also 
        routinely pings the broker to check the connection status. If the
        connection is lost, the thread automatically buffers messages and 
        attempts to reconnect
        """
        global connack
        global incoming_message_buffer
        
        # Setting clean_session = False means that subsciption information and 
        # queued messages are retained after the client disconnects. It is suitable
        # in an environment where disconnects are frequent.
        mqtt_client = mqtt.Client(protocol=self.protocol, client_id=self.name, clean_session=False)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_publish = on_publish
        mqtt_client.on_disconnect = on_disconnect
                
        # Set the LWT
        # If the client disconnects without calling disconnect, the broker will
        # publish this message on its behalf
        # retain should be set to true
        mqtt_client.will_set(self.STATUS, 
                             self.package({'status': STATUS_DISCONNECTED_UNGRACE}), 
                             qos=0, retain=True) 

        # Connect to the broker
        # keepalive is maximum number of seconds allowed between communications
        # with the broker. If no other messages are sent, the client will send a
        # ping request at this interval
        logging.info('Attempting to connect to broker at ' + self.hostname)
        mqtt_client.connect(self.hostname, self.port, keepalive=60)
        
        # Force function to block until connack is sent from the broker, or timeout
        connack = False
        start_time = time.time()
        while not connack:
            time.sleep(0.1)
            mqtt_client.loop()
        
            if time.time() - start_time > timeout:
                raise TimeOutError("The program timed out while trying to connect to the broker!")
                break
        
        # When connected, subscribe to the relevant channels
        mqtt_client.subscribe([(self.PUBLIC, 1), (self.PROTECTED, 1),
                              (self.PRIVATE, 1), (self.PINGREQ, 1),
                              (self.PINGACK, 1), (self.HANDSHAKE, 1)
                             ])
        
        self.client = mqtt_client
        
        # Set a message buffer
        incoming_message_buffer = []

        # Do a blocking call
        self.send_handshake()
        while self.broker_public_key == None:
            time.sleep(0.1)
            mqtt_client.loop()
            # Check the message buffer
            if incoming_message_buffer != []:
                for message in incoming_message_buffer:
                    if message.topic == self.HANDSHAKE:
                        # Check whether it is a broker key message.
                incoming_message_buffer = []
            

        # Start the loop. This method is preferable to repeatedly calling loop
        # since it handles reconnections automatically. It is non-blocking and 
        # handles interactions with the broker in the background.
        logging.info('Starting loop')
        self.client.loop_start()
      
    def send_handshake(self):
        self.client.publish(self.STATUS, 
                            self.package({'status': STATUS_CONNECTED, 
                                          'public_key': self.public_key.exportKey().decode()
                                          }), 
                            qos=1)
                            
    def loop(self):
        """
        This loop method can be run periodically to read messages out of the
        incoming message buffer. It also deals with replying to ping requests
        from other devices.
        
        Note that it is not necessary to handle reconnection to the broker in 
        this function; that task is done by the paho-mqtt loop function. 
        """
        global handshake
        global incoming_message_buffer
        
        # dump all incoming messages into a list and empty the string
        incoming_messages = incoming_message_buffer
        # empty the buffer
        incoming_message_buffer = []

        parsed_messages = []
        pingacks = []
        for message in incoming_messages:
            # Deal with ping requests

            if message.topic == self.PINGREQ:
                self.pingack(json.loads(message.payload.decode()))
            # Deal with acknowledgements to our own ping requests
            elif message.topic == self.PINGACK:
                pingacks.append(json.loads(message.payload.decode()))
            # Parse non-encrypted messages
            elif message.topic == self.PUBLIC:
                parsed_messages.append(json.loads(message.payload.decode()))

        return parsed_messages, pingacks
    
    def clean_up(self):
        # Send a hello message to broker services
        self.client.publish(self.STATUS, 
                     self.package({'status': STATUS_DISCONNECTED_GRACE}), 
                     qos=1)
        self.client.disconnect()
        self.client.loop_stop()
        
        
class BrokerServices(Client):
    def __init__(self, hostname, name, port=1883, protocol='3.1'):
        Client.__init__(self, hostname, name, port, protocol)
        self.devices = {}

    
    def setup(self, timeout=20):
        """
        This method sets up the actual MQTT client, assigns all callback 
        functions for event handling and sets a last will and testament (LWT)
        message. 
        
        It then attempts to connect to the broker. The connection call
        is blocking; it continues until a connection acknowlegement message is 
        received from the broker or until the timeout is reached.
        
        After connection has been acheived, it subscribes to the topics:
            mf2c/[name]/public
            mf2c/[name]/protected
            mf2c/[name]/private
            mf2c/[name]/public/pinreq
            mf2c/[name]/public/pingack
            
        If another device wants to contact this smart agent, it must publish to
        one of these topics. 
        
        Finally, this method starts the MQTT loop running on a separate thread.
        This loop thread handles publishing and receiving messages, and also 
        routinely pings the broker to check the connection status. If the
        connection is lost, the thread automatically buffers messages and 
        attempts to reconnect
        """
        global connack
        global incoming_message_buffer

        # Setting clean_session = False means that subsciption information and 
        # queued messages are retained after the client disconnects. It is suitable
        # in an environment where disconnects are frequent.
        mqtt_client = mqtt.Client(protocol=self.protocol, client_id=self.name, clean_session=False)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_publish = on_publish
        mqtt_client.on_disconnect = on_disconnect

        # Connect to the broker
        # keepalive is maximum number of seconds allowed between communications
        # with the broker. If no other messages are sent, the client will send a
        # ping request at this interval
        logging.info('Attempting to connect to broker at ' + self.hostname)
        mqtt_client.connect(self.hostname, self.port, keepalive=60)
        
        # Force function to block until connack is sent from the broker, or timeout
        connack = False
        start_time = time.time()
        while not connack:
            time.sleep(0.1)
            mqtt_client.loop()
        
            if time.time() - start_time > timeout:
                raise TimeOutError("The program timed out while trying to connect to the broker!")
                break
            
        # Share the broker's public
        mqtt_client.publish(self.BROKER_KEY, 
                            self.package({'public_key': self.public_key.exportKey().decode()}), 
                            qos=1, retain=True)
                            
        # When connected, subscribe to the relevant channels
        mqtt_client.subscribe(self.STATUS, 1)
        
        self.client = mqtt_client
        

                            
        # Set a message buffer
        incoming_message_buffer = []

        # Start the loop. This method is preferable to repeatedly calling loop
        # since it handles reconnections automatically. It is non-blocking and 
        # handles interactions with the broker in the background.
        logging.info('Starting loop')
        self.client.loop_start()
    
    def respond_handshake(self, agent_name):
        self.publish(topic_handshake(agent_name), 
                            self.package({
                                          }), 
                            qos=1)
                            
    def loop(self):
        """
        This loop method can be run periodically to read messages out of the
        incoming message buffer. It also deals with replying to ping requests
        from other devices.
        
        Note that it is not necessary to handle reconnection to the broker in 
        this function; that task is done by the paho-mqtt loop function. 
        """
        global incoming_message_buffer
        
        # dump all incoming messages into a list and empty the string
        incoming_messages = incoming_message_buffer
        # empty the buffer
        incoming_message_buffer = []
        parsed_messages= []

        for message in incoming_messages:
            # Add new devices to the dictionary
            if message.topic == self.STATUS:
                try:
                    payload = json.loads(message.payload.decode())
                    parsed_messages.append(payload)
                    # If we have already met the device...
                    if payload['source'] in self.devices.keys():
                        # And it would like to disconnect...
                        if payload['status'] != 'C':
                            # Remove it from our dictionary
                            del self.devices[payload['source']]
                            logging.info('Device ' + payload['source'] + ' disconnected')
                    # If we do not recognise the device...
                    else:
                        # And it would like to connect...
                        if payload['status'] == 'C':
                            # Add it to our dictionary
                            try:
                                self.devices[payload['source']] = RSA.importKey(payload['public_key'].encode())
                                logging.info('Device ' + payload['source'] + ' connected')
                            except Exception as e:
                                print(e)
                                logging.error(e)
                except:
                    logging.info('Error while reading message: ' + str(message.payload))
        return parsed_messages
    
    def clean_up(self):
        self.client.disconnect()
        self.client.loop_stop()
        
        
if __name__ == "__main__":
    hostname = <name of your host machine>
    port = 1883
    smart_agent = SmartAgent(hostname, '0001')
    smart_agent.setup()
    oldtimestamp = int(timestamp())
    try:
        while True:
            # Believe me, if you don't introduce a delay, this program will 
            # happily take up 90% of your CPU...
            time.sleep(0.1)
            
            # Get the messages in the buffer and deal with ping requests
            messages, pingacks = smart_agent.loop()
            if messages != []:
                for message in messages:
                    print(message)
            
            # Send a message every 10 seconds
            if int(timestamp()) - oldtimestamp >= 10:
                smart_agent.send(['Cheney'], {'payload': "Hello from Emma's Computer"}, security=0, qos=2)
                oldtimestamp = int(timestamp())
    except Exception as e:
        raise e
    finally:
        # clean up
        smart_agent.clean_up()