import re
import select
import logging
import warnings
import struct
import socket
import select
import bluetooth
import bluetooth._bluetooth as _bt

# Note that due to the special characters used by python's re, some
# characters can't be used as delimiters or bookends (although they
# can still be used in normal message payloads) 

class Packet:
    START = '<'
    DIVIDE = '#'
    END = '>'
    COMPONENTS = 3


                       
def check_constants():
    forbidden = ":\.^[]{}()?*+|$" 
    constants = [Packet.START, Packet.DIVIDE, Packet.END]
    if len(set(constants) & set(forbidden)) > 0:
        raise Exception("Forbidden character in constant; you can't use " +
                    "any of " + forbidden + " in the START, " +
                    "END or DIVIDE strings")
    else:
        return True

def check_valid(data):
    """
    Returns True if data contains a single message, and False otherwise.
    """
    regex = (Packet.START + ".+" 
            + (Packet.DIVIDE + ".+")*(Packet.COMPONENTS - 1) 
            + Packet.END)
            
    packaged_messages = re.findall(regex, data.decode(errors="ignore"))
    
    if len(packaged_messages) == 1:
        return True
    elif len(packaged_messages) > 1:
        #warnings.warn("Multiple messages found. Only the first will be used.", RuntimeWarning)
        return True
    else:
        return False
    
    
class Message():
    @classmethod
    def from_components(cls, source, destination, payload):
        obj = cls()
        obj.source = source
        obj.destination = destination
        obj.payload = payload
        return obj

    @classmethod
    def from_packaged(cls, packaged_message):
        obj = cls()
        regex = (Packet.START + "(.+)"
                + (Packet.DIVIDE + "(.+)")*(Packet.COMPONENTS - 1)
                + Packet.END)

        if check_valid(packaged_message):
            # We take the first message in the packet. Note that we will ignore
            # any other valid packets contained in the string
            obj.source, obj.destination, obj.payload = re.findall(regex, packaged_message)[0]
            return obj  
        else:
            raise IOError("Not a valid message!")
        
    def __escape(payload):
        return payload

    def package(self):
        packaged = (Packet.START + self.source
                   + Packet.DIVIDE + self.destination
                   + Packet.DIVIDE + self.payload
                   + Packet.END)
        return packaged

class Device():
    def __init__(self, address, name):
        self.address = address
        self.name = name
        self.subscriptions = set()
        self.sock = None
        
    def fileno(self):
        return self.sock.fileno()
    
    def connect(self):
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

    def send(self, packet):
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
        data = ""

        while True:
            # Loop terminates at timout or error
            try:
                # Read the data in the buffer
                data += self.sock.recv(4096)
                if check_valid(data):
                    return data
                
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

        return None


class Hub():
    # scan_duration must be postive integer. If float, change, if negative, warn and use default
    def __init__(self, address_pattern="SCD_ARDUINO", scan_duration=5):
        self.own_address = self.__get_own_address()
        self.address_pattern = address_pattern
        self.devices = []
        self.scan_duration = scan_duration

    def __error_not_on_network(self, source, destination):
        # Tell source that their destination is not on the network
        return Message.from_components(self.own_address, source, 'Error ' + destination + ' not on network')

    def __reply_list_other_devices(self, source):
        other_devices = [d.address for d in self.devices if d.address != source]
        return Message.from_components(self.own_address, source, 'Reply ' + ' '.join(other_devices))
    
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
        matching_devices = []
        nearby_devices = bluetooth.discover_devices(flush_cache=True, duration=self.scan_duration)
        for device in nearby_devices:
            name = bluetooth.lookup_name(device)
            address = str(device)
            if name == None:
                #logging.info('Unknown device at ' + address)
                pass
            else:
                if name.startswith(self.address_pattern):
                    matching_devices.append(Device(address, name))
        return matching_devices

    
    def update_devices(self):
        """
        There exist three groups of devices:
            1. Those that we discovered in our scan but aren't connected to
            2. Those that we discovered in our scan and are already connected to
            3. Those that we thought we were connected to, but didn't discover in
               our scan

            For now, we will ignore case 3.
        """
        
        matching_devices = self.__scan()

        # MAC addresses are globally unique, so we can use them to truly distinguish
        # between devices

        for match in matching_devices:
            # If we are not already connected to this device...
            if match.address not in [d.address for d in self.devices]:
                # Try to connect. If successful, add device to devices.
                if match.connect() == True:
                    self.devices.append(match)
                
    def handle_message(self, message, verbose=True):

        
        if message.destination == self.own_address:
            if verbose:
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
                    dev.send(message.package())
                    

            # If the intended destination device is not reachable, send an error message
            # back to the source
            if not found_device:
                if verbose:
                    print('Destination not on network. Sending error message to source')
                dev.send(self.__error_not_on_network(message.source, message.destination).package())
                
                    

if __name__ == "__main__":
    myhub = Hub()
    print('Searching for devices')
    myhub.update_devices()
    if len(myhub.devices) > 0:
        for dev in myhub.devices:
            print('Connected to ' + dev.name + ' at ' + dev.address)

        # Select - wait for devices to be ready. When one is, handle messages.
        print('Waiting for packets')
        while True:
            ready_to_read, ready_to_write, ready_with_errors = select.select(myhub.devices, [], [])
            for dev in ready_to_read:
                incoming_packet = dev.receive()
                incoming_message = Message.from_packaged(incoming_packet)
                myhub.handle_message(incoming_message)
                print(incoming_message.payload)
            
    else:
        print('Unable to connect to any devices')
