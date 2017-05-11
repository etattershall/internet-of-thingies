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
import bluetooth
import threading

class NotYetImplemented(Exception):
    def __init__(self, value):
        self.value = value

class FormatError(Exception):
    def __init__(self, value):
        self.value = value

class DeviceError(Exception):
    def __init__(self, value):
        self.value = value
        
def get_time():
    # Required for logging
    now = datetime.datetime.today()
    return now.strftime("%d/%m/%Y %H:%M:%S | ")


class Format:
    """
    Foramt Class contains all information about packet formatting.

    Constants START, DIVIDE and END are characters or character strings used to
    format packets.
    e.g.
    START = '<', DIVIDE = '#' and END = '>' would yield packets in the form:
    <00:00:00:00:00:00#00:00:00:00:00:01#Hello World!>

    When choosing constants, the use of FORBIDDEN characters :\.^[]{}()?*+|$
    must be avoided, since these interact with the regular expressions we use
    in unpredictable ways.

    Notes on class:
    ---------------
    Format has no knowledge of what the internal message components are
    - e.g. 'source', 'destination', 'payload'. It only knows about the external
    packaging of the message string.
    """
    START = '<'
    DIVIDE = '#'
    END = '>'
    ESCAPE = '@'
    FORBIDDEN = ":\.^[]{}()?*+|$" 
    COMPONENTS = 3
    
    def __init__(self):
        pass

    def __check_constants(self):
        """
        Checks that the constants defined in this class are not forbidden

        Parameters
        ----------
        N/A

        Returns
        -------
        bool
            True if the constants are not forbidden
            False otherwise
        """
        constants = [self.START, self.DIVIDE, self.END, self.ESCAPE]
        if len(set(constants) & set(self.FORBIDDEN)) > 0:
            return False
        else:
            return True

    def __escape(self, data):
        """
        If the START, DIVIDE or END constants are present in the message
        payload, it will cause problems when the message is unpackaged
        unless these constants are escaped.

        To escape a character, we add the ESCAPE string before it. We
        must also escape any characters matching the escape string itself.

        Parameters
        ----------
        data: str
            Plaintext string, normally a message payload which may or may
            not contain reserved characters

        Returns
        -------
        str
            Escaped string in which all reserved characters are preceded by the
            ESCAPE character.
            
        """
        # Must escape escapes first (otherwise everything else will be
        # escaped twice!)
        data = re.sub(self.ESCAPE, 2*self.ESCAPE, data)
        reserved = [self.START, self.DIVIDE, self.END]
        for char in reserved:
            data = re.sub(char, self.ESCAPE + char, data)
        return data

    def __unescape(self, data):
        """
        Reserved characters such as START, END and DIVIDE cause problems
        when messages are unpacked. Therefore, they have been escaped. This
        function removes ESCAPE characters preceding reserved characters
        from an input string

        Parameters
        ----------
        data: str
            Plaintext string, normally a message payload which may or may
            not contain escaped reserved characters

        Returns
        -------
        str
            Unescaped string in which all reserved characters have been stripped
            of the escape character
            
        """
        reserved = [self.START, self.DIVIDE, self.END]
        for char in reserved:
            data = re.sub(self.ESCAPE + char, char, data)
        # Must unescape escapes last
        data = re.sub(2*self.ESCAPE, self.ESCAPE, data)
        return data
    
    def find_packets(self, data):
        """
        Checks to see if any packets in the required format are contained in the
        data presented. If no packets are present, an empty list is returned.

        Parameters
        ----------
        data: bytes
            Plaintext string which may or may not contain a message packet

        Returns
        -------
        list of lists of strings
            Returns a list of valid packets. Each packet is a list of components.
            e.g.
            [[source1, destination1, payload1], [source2, destination2, payload2],...]        
        """

        packets = []
        current_packet = []
        current_component = ""
        reserved = [self.START, self.DIVIDE, self.END, self.ESCAPE]
        char_is_escaped = False
        inside_packet = False
        for char in data.decode(errors="ignore"):
            # If the previous character was the escape character...
            if char_is_escaped:
                # Nothing to see here, move along.
                if inside_packet:
                    current_component += char
                    char_is_escaped = False
                else:
                    char_is_escaped = False
            else:
                # If the current character is the escape character (and is not itself escaped)...
                if char == self.ESCAPE:
                    char_is_escaped = True
                    if inside_packet:
                        current_component += char
                elif char == self.START:
                    if inside_packet:
                        # Something is very wrong...
                        # Empty out the current packet and start again
                        current_packet = []
                        current_component = ""
                    else:
                        inside_packet = True
                elif char == self.END:
                    if inside_packet:
                        # Tie off this packet and add it to the pile
                        current_packet.append(current_component)
                        packets.append(current_packet)
                        # Clear out the old data
                        current_packet = []
                        current_component = ""
                    else:
                        pass
                elif char == self.DIVIDE:
                    if inside_packet:
                        # We are going to start a new component!
                        current_packet.append(current_component)
                        # Clear out the old data
                        current_component = ""
                    else:
                        pass
                else:
                    if inside_packet:
                        current_component += char
                    else:
                        pass
    
        
        unescaped_packets = []
        for packet in packets:
            # Ignore packets with the wrong number of components
            if len(packet) == self.COMPONENTS:
                # The components must be unescaped before they are passed on
                unescaped_packets.append([self.__unescape(c) for c in list(packet)])
        return unescaped_packets


                       
    def package(self, components):
        """
        Takes a list of message components and packages them using the chosen
        format
        e.g.
        ['00:00:00:00:00:00', '00:00:00:00:00:01', 'Hello World']
            --> '<00:00:00:00:00:00#00:00:00:00:00:01#HelloWorld>#'

        Also escapes any reserved characters in any of the components
        
        Parameters
        ----------
        components: list of strings
            List of message components in the agreed-upon order

        Returns
        -------
        str
            Packet
            
        """
        if len(components) != self.COMPONENTS:
            raise Exception('Wrong number of components!')
        # Escape all components
        escaped_components = [self.__escape(c) for c in components]
        packet = self.START + escaped_components[0]
        for c in escaped_components[1:]:
            packet += self.DIVIDE + c
        packet += self.END
        return packet
    
    
    
class Message():
    """
    Class contains all the information about the contents of packets.
    
    A message is an object with a source, an intended destination and
    a payload.
    
    Notes on class:
    ---------------
    Message has no knowledge about how the packets are formatitted -
    e.g. <###>; or about how characters are escaped. All of that is handled
    by the Format class.

    The main responsibility of this class is knowing the *order* of the
    transmitted message components. If more components are added, then the order
    will have to be changed in this class.
    """
    def __init__(self, components):
        self.source = components[0]
        self.destination = components[1]
        self.payload = components[2]
        
    def components(self):
        """
        Returns a list of message components in the correct order

        Parameters
        ----------
        N/A

        Returns
        -------
        list of strings
            Ordered message components   
        """
        components = [self.source, self.destination, self.payload]
        return components
    
class Device():
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
    def __init__(self, name):
        self.name = name
        self.subscriptions = set()
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
            

    def send(self, components):
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
        packet = Format().package(components)
        try:
            self.sock.send(packet)
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
                packets = Format().find_packets(data)
                
                if len(packets) > 0:
                    return packets, None
                
            except Exception as e:
                # When there is no more data to read, we get Bluetooth error
                # In this case, we can wait a little while to see if more data is
                # transmitted
                return '', e

        # Error handling if no packet is received        
        if len(data) > 0:
            return '', FormatError("Listen timeout: data received but incorrectly packaged. " +
                        "data: " + data.decode(errors="ignore"))
        else:
            return '', DeviceError("Listen timeout: no data transmitted!")

        return []

class BluetoothDevice(Device):
    """
    Extension of the Device class
    
    Handles Bluetooth-specific connections
    """
    def __init__(self, name, address):
        Device.__init__(self, name)
        self.address = address
    
    def connect(self):
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
                



        
        
class TCPDevice(Device):
    def __init__(self, name, port):
        Device.__init__(self, name)
        self.port = port

    def get_ip_address(self):
        # Since some of the computers in the network use dynamic IP addresses, it
        # is better to start with a name and find the IP
        try:
            self.address = socket.gethostbyname(self.name)
            return None
        except Exception as e:
            return e
      
    
    def connect(self, timeout):
        
        # Attempt to create the connection
        
        try:
            self.sock = socket.create_connection((self.address, self.port), timeout=timeout)
            return None
        except Exception as e:
            # socket.timeout is a common error
            return e


class Switch():
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
        self.address_pattern = address_pattern
        self.devices = []
        
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
    
    def __relay_local_packet(self, packet, device):
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
                    
    def device_manager(self):
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
            flag = dev.connect()
            
            if flag is None:
                self.devices.append(dev)
                print("Successfully connected!")
            else:
                # For now, we report all errors as we find them. Later they
                # will just be logged.
                print(flag)

        # If we have at least two devices, sleep for a while so they can chat
        if len(self.devices) >= 2:
            time.sleep(20)
        else:
            print("Too few devices on network: we are only connected to " + str(len(self.devices)) + " devices")


    def message_manager(self):
        # This function needs to be run in a thread
        # Waits for devices to be ready to send information, and then receives
        # from them and handles their messages.

        # Does it have to spawn a new thread every time it needs to relay a message?

        if len(self.devices) > 0:
            print("Waiting for the next event")
            ready_to_read, ready_to_write, ready_with_errors = select.select(self.devices, [], [])
            for ready_device in ready_to_read:
                #logging.info(get_time() + 'Device ' + dev.name + ' at ' + dev.address + ' is ready to read.')
                packets, flag = ready_device.receive()
                
                if flag is None:
                    for packet in packets:
                        #logging.info(get_time() + 'Read packet from ' + dev.name + ' at ' + dev.address + '.')
                        message = Message(packet)
                        print("Received packet from " + ready_device.address)
                        # Send the message on. 
                        for dev in self.devices:
                            if message.destination == dev.address:
                                self.__relay_local_packet(packet, dev)
                else:
                    #logging.warning(get_time() + 'Unable to read from ' + dev.name + ' at ' + dev.address + '.')
                    raise flag
        else:
            # Not able to connect to any devices!
            # Do not print, or will happen endlessly...
            pass

    def monitor(self):
        # Debugging thread: prints out the devices currently connected
        time.sleep(3)
        print("Connected to " + " ,".join([d.address for d in self.devices]))
        
    def shutdown(self):
        # Terminate threads and gracefully close all connections
        for dev in self.devices:
            dev.disconnect()
        


class SwitchPlus(Switch):
    # Attempts to connect to a coordinator
    # If successful, connects to any available BT devices matching its address pattern
    # Relays packets between nodes on local network
    # Sends traffic to unknown addresses up to Coordinator
    # Replies to Coordinator if necessary.
    def __init__(self, address_pattern, host_name, port):
        #self.coordinator = None
        #self.public_key = ''
        #self.private_key = ''
        #self.coordinator_public_key = ''
        raise NotYetImplemented()
    def __reply_to_coordinator(self, payload):
        raise NotYetImplemented()
    def __send_packet_up(self, packet):
        raise NotYetImplemented()
    def __encrypt(self, payload):
        # Traffic sent up to coordinator should be encrypted with
        # own public key
        raise NotYetImplemented()
    def __decrypt(self, payload):
        # The coordinator sends encrypted messages. Decrypt using own private key.
        raise NotYetImplemented()
        
    def __find_coordinator(self):
        raise NotYetImplemented()
            
    def switchplus_loop(self, logging=True):
        # if coordinator is None:
            # Try to connect to coordinator
        # else:
            # use switch_loop
        raise NotYetImplemented()

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

    # Start logging
    LOG_FILENAME = 'hub_log.out'
    logging.basicConfig(
        filename=LOG_FILENAME,
        level = logging.DEBUG,
        )
    
    #logging.info(get_time() + 'Started hub program')

    # Initialise switch    
    myswitch = Switch(address_pattern='SCD_ARDUINO')

    # Start off both threads
    try:
        while True:
            scan_thread = threading.Thread(target=myswitch.device_manager(), daemon=True)
            relay_thread = threading.Thread(target=myswitch.message_manager(), daemon=True)
            monitor_thread = threading.Thread(target=myswitch.monitor(), daemon=True)
            
            scan_thread.start()
            relay_thread.start()
            monitor_thread.start()
        
    except KeyboardInterrupt:
        print("Ctrl-C Pressed!")
    finally:
        myswitch.shutdown()
        print("All devices disconnected.")
    

    #logging.info(get_time() + 'Started Hub')


    # FINALLY
    
    
