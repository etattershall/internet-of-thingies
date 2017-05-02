import re
import datetime
import select
import logging
import warnings
import struct
import socket
import select
import bluetooth
import bluetooth._bluetooth as _bt


def get_time():
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
        data: str
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
    def __init__(self, address, name):
        self.address = address
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
        success = False
        try:
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.connect((self.address, 1))
            sock.settimeout(2.0)

            # Actually, if the socket is set to be non-blocking, it terminates
            # immediately with an error if there is no data to be read
            #sock.setblocking(0)

            self.sock = sock
            success = True
            
        except bluetooth.BluetoothError as e:
            print(e)
            
        if success:
            return True
        else:
            return False

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
        success = False
        try:
            self.sock.close()
            success = True
            
        except bluetooth.BluetoothError as e:
            print(e)
                
        if success:
            return True
        else:
            return False

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
        success = False
        try:
            self.sock.send(packet)
            success = True
            
        except bluetooth.BluetoothError as e:
            print(e)
        if success:
            return True
        else:
            return False

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
        
        data = ""

        while True:
            # Loop terminates at timout or error
            try:
                # Read the data in the buffer
                data += self.sock.recv(4096)
                packets = Format().find_packets(data)
                if len(packets) > 0:
                    return packets
                
            except bluetooth.BluetoothError as e:
                # When there is no more data to read, we get Bluetooth error
                # In this case, we can wait a little while to see if more data is
                # transmitted
                return e

        # Error handling if no packet is received        
        if len(data) > 0:
            raise Error("Listen timeout: data received but incorrectly packaged. " +
                        "data: " + data.decode(errors="ignore"))
        else:
            raise Error("Listen timeout: no data transmitted!")

        return []


class Hub():
    """
    The Hub class handles a list of devices. It also relays messages between
    devices and responds to messages sent to itself.
    """
    # Set default scan duration
    scan_duration = 5
    def __init__(self, address_pattern="SCD_ARDUINO", scan_duration=5):
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
        self.own_address = self.__get_own_address()
        self.address_pattern = address_pattern
        self.devices = []

        # Error handling for scan duration
        # If not an integer, attempt to integerise it. If not positive
        # or equal to zero, leave the scan duration as default.
        if type(scan_duration) != int:
            try:
                scan_duraton = int(scan_duration)
                if scan_duration > 0:
                    self.scan_duration = scan_duration
            except:
                #LOGGING
                pass
        else:
            if scan_duration > 0:
                self.scan_duration = scan_duration
        

    def __error_not_on_network(self, source, destination):
        """
        Assembles a message to be sent to a device to inform them that
        their message could not be sent because their intended recipient
        is not on the network
        
        Parameters
        ----------
        source: str
            MAC address of device sending undeliverable message
        destination: str
            MAC address of the intended recipient of the original message.
            
        Returns
        -------
        Message
            Message object ready to be packaged and sent back to the
            original source address
        """
        payload = 'Error ' + destination + ' not on network'
        return Message([self.own_address, source, payload])

    def __reply_list_other_devices(self, source):
        """
        Assembles a message containing a list of other devices on the
        network
        
        Parameters
        ----------
        source: str
            MAC address of querying device

        Returns
        -------
        Message
            Message object ready to be packaged and sent back to the
            source address
        """
        other_devices = [d.address for d in self.devices if d.address != source]
        payload = 'Reply ' + ' '.join(other_devices)
        return Message([self.own_address, source, payload])
    
    def __get_own_address(self):
        """
        Adapted from pybluez documentation
        (pybluez/examples/advaced/read-local-bdaddr)

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
        hci_sock = _bt.hci_open_dev(0)
        old_filter = hci_sock.getsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, 14)
        flt = _bt.hci_filter_new()
        opcode = _bt.cmd_opcode_pack(_bt.OGF_INFO_PARAM, 
                _bt.OCF_READ_BD_ADDR)
        _bt.hci_filter_set_ptype(flt, _bt.HCI_EVENT_PKT)
        _bt.hci_filter_set_event(flt, _bt.EVT_CMD_COMPLETE);
        _bt.hci_filter_set_opcode(flt, opcode)
        hci_sock.setsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, flt )

        _bt.hci_send_cmd(hci_sock, _bt.OGF_INFO_PARAM, _bt.OCF_READ_BD_ADDR )

        pkt = hci_sock.recv(255)

        status,raw_bdaddr = struct.unpack("xxxxxxB6s", pkt)
        assert status == 0

        t = [ "%X" % ord(b) for b in raw_bdaddr ]
        t.reverse()
        bdaddr = ":".join(t)

        # restore old filter
        hci_sock.setsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, old_filter )
        return bdaddr.encode('ascii', 'ignore')

    def __scan(self):
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
                    matching_devices.append(Device(address, name))
        return matching_devices

    
    def update_devices(self):
        """
        Uses scan function to find nearby devices whose friendly names match
        the address pattern. Attempts to connect to matching devices. If successful,
        appends the new device to the list of devices.
        
        Parameters
        ----------
        N/A
            
        Returns
        -------
        N/A
            
        Method notes
        ------------
        There exist three groups of devices:
            1. Those that we discovered in our scan but aren't connected to
            2. Those that we discovered in our scan and are already connected to
            3. Those that we thought we were connected to, but didn't discover in
               our scan

            For now, we will ignore case 3.
        """
        
        matching_devices = self.__scan()
        logging.info(get_time() + 'Found ' + str(len(matching_devices)) + ' matching devices')
        # MAC addresses are globally unique, so we can use them to truly distinguish
        # between devices

        for match in matching_devices:
            # If we are not already connected to this device...
            if match.address not in [d.address for d in self.devices]:
                # Try to connect. If successful, add device to devices.
                if match.connect() == True:
                    self.devices.append(match)
                else:
                    logging.warn(get_time() + 'Unable to connect to device '
                                 + match.name + ' at ' + match.address + '.')
                
    def handle_message(self, message, verbose=True):
        """
        Takes a message input.

        Two cases:
        - Message destination is hub: hub replies as appropriate
        - Message destination is not hub: hub relays message. If
          unsuccessfull, an error message is sent to the source.

        Parameters
        ----------
        message: Message
            A received message object
        verbose: bool
            If verbose, information is printed to the terminal

        Returns
        -------
        N/A
        """
        if message.destination == self.own_address:
            if verbose:
                logging.info(get_time() + 'Message is for hub: ' + message.content)
                print('Message is for hub')
            # 1. Ask who else is here?
            # 2.
            pass
        else:
            # Relay the message
            found_device = False
            for dev in self.devices:
                if dev.address == message.destination:
                    found_device = True
                    if verbose:
                        print('Relaying message to destination')
                    if dev.send(message.components()):
                        logging.info(get_time() + 'Relayed message to destination')
                    else:
                        logging.warning(get_time() + 'Not able to relay message to destination')
                    

            # If the intended destination device is not reachable, send an error message
            # back to the source
            if not found_device:
                if verbose:
                    print('Destination not on network. Sending error message to source')
                logging.info(get_time() + 'Device is not on network. Sending error message back to source')
                dev.send(self.__error_not_on_network(message.source, message.destination).package())
                
                    

if __name__ == "__main__":

    # Start logging
    LOG_FILENAME = 'hub_log.out'
    logging.basicConfig(
        filename=LOG_FILENAME,
        level = logging.DEBUG,
        )
    
    logging.info(get_time() + 'Started hub program')
    
    myhub = Hub()
    logging.info(get_time() + 'Started Hub')
    
    print('Searching for devices')
    logging.info(get_time() + 'Searching for devices...')
    myhub.update_devices()
    
    if len(myhub.devices) > 0:
        for dev in myhub.devices:
            print('Connected to ' + dev.name + ' at ' + dev.address)
            logging.info(get_time() + 'Connected to device ' + dev.name + ' at ' + dev.address + '.')


        # Select - wait for devices to be ready. When one is, handle messages.
        print('Waiting for packets')
        while True:
            ready_to_read, ready_to_write, ready_with_errors = select.select(myhub.devices, [], [])
            for dev in ready_to_read:
                logging.info(get_time() + 'Device ' + dev.name + ' at ' + dev.address + ' is ready to read.')
                packets = dev.receive()

                if len(packets) > 0:
                    logging.info(get_time() + 'Read packet from ' + dev.name + ' at ' + dev.address + '.')
                    message = Message(packets[0])
                    myhub.handle_message(message)
                    print(message.payload)
                else:
                    logging.warning(get_time() + 'Unable to read from ' + dev.name + ' at ' + dev.address + '.')
            
    else:
        print('Unable to connect to any devices')
