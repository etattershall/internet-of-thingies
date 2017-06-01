import sys
import subprocess
import re
import time
import datetime
import select
import logging
import warnings
import struct
import socket
import select
import serial
import json
import bluetooth
import threading
import serial.tools.list_ports

class NotYetImplemented(Exception):
    def __init__(self, value):
        self.value = value

class FormatError(Exception):
    def __init__(self, value):
        self.value = value

class DeviceError(Exception):
    def __init__(self, value):
        self.value = value

class AuthenticationError(Exception):
    def __init__(self, value):
        self.value = value
        
def get_time():
    # Required for logging
    now = datetime.datetime.today()
    return now.strftime("%d/%m/%Y %H:%M:%S | ")

def serial_scan(address_pattern):
    # Returns a list of com ports connected to arduinos
    matching_ports = []
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        if port.description.startswith(address_pattern):
            matching_ports.append(port.device)
    return matching_ports
        
class BluetoothDevice():
    """
    Device class is a wrapper for a Bluetooth socket. Defining this as a
    class allows us to keep track of sockets when they are passed to
    the select function.

    Most importantly, the class has the method:
        def fileno(self):
            return self.sock.fileno
    This method must not be removed - it means that select sees a Device object
    as a socket.
    
    This class handles all direct interaction with sockets. 
    """
    def __init__(self, name, address):
        self.name = name
        self.subscriptions = set()
        self.address = address
        self.sock = None
        
    def fileno(self):
        """
        Returns integer file descriptor that is used by the underlying
        implementation to request I/O operations from the operating system

        MUST BE LEFT IN, OR SELECT WILL NOT WORK ON DEVICES
        """
        return self.sock.fileno()

    def disconnect(self):
        """
        Attemps to disconnect from the device. Does not delete the socket.
        
        Parameters
        ----------
        N/A

        Returns
        -------
        bool
            True if successful
            False otherwise
        """
        try:
            self.sock.close()
            return None
            
        except Exception as e:
            return e
            

    def send(self, message):
        """
        Attemps to send a message to the device.

        Uses Format to package the message components
        
        Parameters
        ----------
        components: list of strings
            

        Returns
        -------
        bool
            True if successful
            False otherwise
        """
        packet = json.dumps(message)
        try:
            self.sock.send(packet.encode('utf-8'))
            return None
            
        except Exception as e:
            return e
            

    def receive(self):
        """
        Attemps to receive a message from the socket.

        Receives data in chunks. Once it has a full packet
        (indicated by Format().find_packets returning a non-empty
        response), it returns the packet. 

        If the timout is reached before a message is delivered,
        receive returns an empty list
        
        Parameters
        ----------
        N/A
            

        Returns
        -------
        list of lists
            The packets received from the socket.
        """
        
        data = b""

        while True:
            # Loop terminates at timout or error
            try:
                # Read the data in the buffer
                data += self.sock.recv(4096)
                try:
                    message = json.loads(data)
                except json.JSONDecodeError as e:
                    message = None
                
                return message, ''
                
            except Exception as e:
                # When there is no more data to read, we get Bluetooth error
                # In this case, we can wait a little while to see if more data is
                # transmitted
                return None, e

        # Error handling if no packet is received        
        if len(data) > 0:
            return None, FormatError("Listen timeout: data received but incorrectly packaged. " +
                        "data: " + data.decode(errors="ignore"))
        else:
            return None, DeviceError("Listen timeout: no data transmitted!")

        return []

    def connect(self, timeout):
        """
        Attemps to connect to the bluetooth device with the address
        contained in self.address.

        This method is defined separately from init to allow for greater
        flexibility (e.g. keeping information about devices that we are
        not currently connected to.)
        
        Parameters
        ----------
        N/A

        Returns
        -------
        bool
            True if successful
            False otherwise
        """

        try:
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            # The line below will not work on a Windows system because of the limitations
            # of Bluez - unable to set socket options.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #sock.settimeout(5)
            sock.connect((self.address, 1))
            

            self.sock = sock
            return None
            
            
        except Exception as e:
            # Setting a timeout causes an error to be thrown even if the connection
            # is made. In this case, ignore the error and carry on.
            if str(e) == "(77, 'File descriptor in bad state')":
                self.sock = sock
                return None
            else:
                return e

    def still_connected(self):
        """
        Checks if the device is still actually available
        (e.g. if it has powered down or moved out of range it won't be,
        but communications will fail).

        Tests availability using the getpeername method, which returns an
        error if the device is not longer available

        Parameters
        ----------
        N/A

        Returns
        -------
        bool
            True if connected
            False otherwise
        """
        try:
            self.sock.getpeername()
            return True
        except bluetooth.BluetoothError as e:
            # Rather than returning this error, we just use it to test
            # whether the socket still links to an endpoint
            return False

class SerialDevice():
    def __init__(self, comport):
        self.name = None
        self.subscriptions = set()
        self.comport = comport
        self.ser = None

    def connect(self, timeout=0):
        # Attempt to open a serial connection to the device
        try:
            self.ser = serial.Serial(self.comport, 9600, timeout=timeout)
            return None
        except Exception as e:
            return e
      
    def handshake(self, my_key, their_key):
        # Ask the device to authenticate
        message = {
            'source': 'sink',
            'type': 'handshake',
            'payload': my_key
        }
        flag = self.send(message)
        if flag:
            return flag
            
        # Wait until the device returns a response
        while True:
            # Check if the device has data waiting to be read
            if self.ser.in_waiting:
                # Receive a single message
                response = self.receive()


                if response['type'] == 'handshake':
                    if response['payload'] == their_key:
                        self.name = response['source']
                        return None
                    else:
                        return AuthenticationError("Wrong password")
                else:
                    return AuthenticationError("Incorrect response to handshake: " + response['type'])
            break
                
    def receive(self):
        """
        Receives a single message
        """
        data = ''
        while True:
            data += self.ser.readline().decode(errors='ignore').strip()
            # Note: this program cannot cope with internal '{}' brackets inside the json, so be sure not
            # to use them in the plaintext when composing a message!
            potential_messages = re.findall('\{[^\{\}]+\}', data)
            for potential_message in potential_messages:
                try:
                    message = json.loads(potential_message)
                    # json loads is a bit of a blunt instrument. It will interpret "hi" as a 
                    # jsonic object! 
                    if type(message) == dict:
                        return message

                except Exception as e:
                    pass
        
                    
    def send(self, message):
        packet = json.dumps(message).encode('ascii')
        try:
            self.ser.write(packet)
            return None
        except Exception as e:
            return e
        
            

class Server():
    def __init__(self):
        self.devices = []
        
    def relay_local_packet(self, packet, device):
        # If a packet is destined for one of the switch's own dependent devices, forward
        # it to that device

        # Is this redundant? Is functionality already handled bu Device class?
        flag = device.send(packet)
        if flag is None:
            print('Packet sucessfully sent')
        else:
            raise flag

    def __prune_devices(self):
        # Remove devices that are no longer available
        # Devices that we are connected to do not show up in scans.
        # Therefore, we want to go through the list of connected devices and
        # prune any which have left.

        # Later, we may want to keep a list of previously connected devices
        
        current_devices = []
        for device in self.devices:
            if device.still_connected:
                current_devices.append(device)
            else:
                # Close up shop...
                device.disconnect()
        self.devices = current_devices
        
    def shutdown(self):
        # Terminate threads and gracefully close all connections
        for dev in self.devices:
            dev.disconnect()



class BTServer(Server):
    # Connects to any available BT devices matching its address pattern
    # Relays packets between nodes in local network

    def __init__(self, address_pattern, scan_duration=5):
        """
        Initialise a hub
        
        Parameters
        ----------
        address_pattern: string
            
        scan_duration: positive int
            (default = 5)
            If the scan duration is not a positive int, the scanner will hang!
            
        Returns
        -------
        N/A
        """
        Server.__init__(self, name)
        self.address_pattern = address_pattern
        
        # Error handling for scan duration
        # If not an integer, attempt to integerise it. If not positive
        # or equal to zero, leave the scan duration as default.
        if type(scan_duration) != int:
            try:
                scan_duration = int(scan_duration)
                if scan_duration > 0:
                    self.scan_duration = scan_duration
            except:
                self.scan_duration = 5
                #LOGGING
                pass
        else:
            if scan_duration > 0:
                self.scan_duration = scan_duration

    def __get_own_address(self):
        """
        Checks local device (device id = 0) and returns the bluetooth
        address. 

        Parameters
        ----------
        None

        Returns
        -------
        string
            Bluetooth address in the form: 
            '88:53:2E:86:BE:8C'

        """
        mac = ''
        if sys.platform.startswith("win"):
            interfaces = subprocess.check_output(["getmac", "/V"]).decode().split("\n")
            for interface in interfaces:
                if interface.startswith("Bluetooth"):
                    macs = re.findall("[A-Z0-9]{2}" + "-[A-Z0-9]{2}"*5, interface)
                    if len(macs) > 0:
                        mac = macs[0].replace('-', ':')

        elif sys.platform.startswith("linux"):
            interfaces = subprocess.check_output(["hcitool", "dev"]).decode().split("\n")
            for interface in interfaces:
                if interface.strip().startswith("hci"):
                    mac = re.findall("[A-Z0-9]{2}" + ":[A-Z0-9]{2}"*5, interface)[0]
        #mac = ':'.join(("%012X" % uuid.getnode())[i:i+2] for i in range(0, 12, 2))
        return mac.encode('ascii', 'ignore')
    
        
    def __scan(self):
        # As in Hub. Should be scanning in background and spawn new process if 
        # an unknown device with the correct address pattern is found
        """
        Search for nearby Bluetooth devices whose friendly names match the
        chosen address pattern.
        
        Parameters
        ----------
        N/A
            
        Returns
        -------
        list of Devices
            List of MAC addresses of matching devices
        """
        matching_devices = []
        nearby_devices = bluetooth.discover_devices(flush_cache=True, duration=self.scan_duration)
        for device in nearby_devices:
            name = bluetooth.lookup_name(device)
            address = str(device)
            if name != None:
                if name.startswith(self.address_pattern):
                    matching_devices.append(BluetoothDevice(name, address))
        return matching_devices
    

                    
    def update_devices(self):
        # This function will need to be run in a thread
        # Continually scans for devices using __scan
        # Updates our list of devices

        # Remove devices that are no longer active
        
        print("Removing unavailable devices")
        self.__prune_devices()

        # Scan for new devices
        print("Scanning")
        new_devices = self.__scan()

        print("Discovered " + str(len(new_devices)) + " new devices")
        # Add new devices:
        for dev in new_devices:
            # Attempt to connect
            print("Attempting to connect to device " + dev.address)
            flag = dev.connect(timeout=5)
            
            if flag is None:
                self.devices.append(dev)
                print("Successfully connected!")
            else:
                # For now, we report all errors as we find them. Later they
                # will just be logged.
                print(flag)



class Coordinator():
    # Maintains a routing table
    # Waits to be connected to via TCP (does not scan)
    # Routes traffic to distant nodes
    # Coordinator must always be listening and must accept all connections
    # (ignore authentication for now
    def __init__(self):
        self.routing_table = {}
        # Later, when we implement authentication, Coordinator will compile
        # a list of Swich devices' public keys
        #self.device_public_keys = {}
        raise NotYetImplemented()
    def __update_routing_table(self, message_source, message_sender):
        self.routing_table[message_source] = message_sender
    def loop(self, logging=True):
        raise NotYetImplemented()

if __name__ == "__main__":
    pass
