from __future__ import print_function, absolute_import, division

import os
import sys
import re
import warnings
import socket, struct
import time

import bluetooth
import bluetooth._bluetooth as _bt




def notes():
    """
    Stuff that will need to be in the __init__ docstring


    Raspberry Pi setup notes:
    -------------------------

    rfcomm servers and clients will initially hang with the error
    BluetoothError: (115, 'Operation now in progress')

    This is an issue with the bluez default settings in ubuntu/debian
    (bediyap.com/linux/bluez-client-server-in-debian/)

    Fix by editing /etc/bluetooth/main.conf
    add:
    DisablePlugins = pnat

    and restart with
    sudo invoke-rc.d bluetooth restart

    This causes the program to throw a different error
    BluetoothError: (113, 'No route to host')
    But now I think about it, that might be beacause of password...
    YES, it was because of password


    """

def read_local_bdaddr():
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

    
def scan(address_pattern, duration=3, verbose=False): 
    """
    Scans for nearby bluetooth devices and returns a list of addresses

    Parameters
    ----------
    address_pattern : str
        The agreed upon string that all the HC05 chips' names start with
        e.g SCD_ARDUINO. Any device with a name matching this pattern is
        returned.
    duration: int
        The maximum scan duration. I've found that in cases where there is a
        good signal (HC05 close to Pi), duration=1 finds the devices.
    verbose: bool
        If True, provides printed output about all nearby devices

    Returns
    -------
    list
        List of bluetooth addresses; 
        e.g ['88:53:2E:86:BE:8C', '00:15:83:B6:76:CE'...]

    """
    if duration == 0:
        raise IOError("Duration must be a postive integer greater than zero. "+
                      "If you pass zero, the program will hang!")
    addresses = []
    nearby_devices = bluetooth.discover_devices(flush_cache=True, duration=duration)
    for device in nearby_devices:
        name = bluetooth.lookup_name(device)
        if name == None:
            if verbose:
                print('Unknown at MAC address ' + str(device))
        else:
            if verbose:
                print(name + ' at MAC address ' + str(device))
            if name.startswith(address_pattern):
                addresses.append(str(device))
    return addresses

def connect(address):
    """
    Takes a bluetooth address and attempts to create a socket to
    connect to it

    Notes
    ----------
    It's not easy to connect to a passkey-protected device programmatically,
    because pybluez does not provide a facility for it - authentication
    is managed by the os. For now we are ignoring passkeys; later we
    will have to write a shell script (or similar?) to call if authentication
    fails
    
    Parameters
    ----------
    address : str
        The bluetooth address of the module we want to connect
        to; e.g. '88:53:2E:86:BE:8C'

    Returns
    -------
    BluetoothSocket
        The bluetooth socket 
    """ 
    
    if not bluetooth.is_valid_address(address):
        raise IOError("Address formatted incorrectly")

    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    
    # The line below allow allows for the reuse of addresses and
    # ports. It should hopefully prevent port already in use errors.
    # Documentation is at www.delorie.com/gnu/docs/glibc/libc_352.html
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.connect((address,1))

    # Set a timeout. This may need to be added as an argument to this
    # function
    sock.settimeout(2.0)
    
    # Set the socket as non-blocking. This means that if we call listen(),
    # and the socket doesn't send anything, then it doesn't throw an error
    sock.setblocking(0)
    
    return sock

def disconnect(sock):
    """
    Closes a bluetooth socket, handles errors

    Parameters
    ----------
    address : BluetoothSocket
        An open bluetooth socket

    Returns
    -------
    bool
        True if successful
    """ 
    sock.close()
    return True


def package(source, destination, message, MAX_LENGTH=1024):
    """
    Packages a given message using the pattern;
    '<source|destination|message>'

    Notes
    ----------
    If the characters '|', '<' or '>' are present in the message, they
    will be removed and a warning will be raised.
    
    Parameters
    ----------
    source : str
        The bluetooth address of this device
    destination : str
        The address of the open, connected socket that we
        want to send the message to.
    message : str
        The message to send. Must contain no '|', '>' or '<' characters.
        
    Returns
    -------
    str
        The packaged message in the form
        '<source|destination|message>'
    """
    # check message for errors (e.g. extra |)
    if '|' in message:
        message = message.replace('|', ' ')
        warnings.warn("Forbidden character '|' removed from message")
    if '<' in message or '>' in message:
        message = re.sub('[<>]', '', message)
        warnings.warn("Forbidden character '<' or '>' removed from message")
    if len(message) > MAX_LENGTH:
        raise IOError("Message greater than max message length")
    if not bluetooth.is_valid_address(source):
        raise IOError("Source address formatted incorrectly")
    if not bluetooth.is_valid_address(destination):
        raise IOError("Destination address formatted incorrectly")
    
    return '<'+source+'|'+destination+'|'+message+'>'


def unpackage(packaged_message):
    """
    Takes a packaged message in the form
    '<source|destination|message>' 
    and returns the separate components

    Parameters
    ----------
    packaged_message : str
        The packaged message in the form '<source|destination|message>'

    Returns
    -------
    str
        source
    str
        destination
    str 
        message
    """
    if not packaged_message.startswith('<') or not packaged_message.endswith('>'):
        raise IOError("Invalid message: not bookended with '<>'")
    if len(packaged_message.split('|')) != 3:
        raise IOError("Invalid message: wrong number of components")
    
    # Remove triangular brackets
    packaged_message = re.sub('[<>]', '', packaged_message)
    source, destination, message = packaged_message.split('|')
    return source, destination, message


def send_message(sock, packaged_message):
    """
    Takes a packaged message in the form
    '<source|destination|message>' 
    and returns the separate components

    Notes
    ----------
    Need to add some strong error handling
    Scenarios:
    - Device moves out of range/disconnects
    
    Parameters
    ----------
    socket: BluetoothSocket
        An open bluetooth socket
    
    packaged_message : str
        The packaged message in the form '<source|destination|message>'

    Returns
    -------
    bool
        True: success
        False: fail

    """
    sock.send(packaged_message)
    return True

def listen(sock):
    """
    Listens at a socket until it receives a message, or until it times out
    
    Parameters
    ----------
    socket: BluetoothSocket
        An open bluetooth socket
    
    Notes
    -----
    While we do not spcify a timeout, the while-loop
    will automatically terminate after a period with
    BluetoothError: timed out

    Returns
    -------
    str
        The packaged message received from the socket.
        

    """
    # Initialise a variable to store incoming data in
    data = ''
    while True:
        data += sock.recv(4096)
        print(data)
        # Find any sting matching the message pattern <|||> in the data
        # Later, errors should be logged
        packaged_message = re.findall('<(.+|.+|.+)>', data.decode(errors="ignore"))
        if len(packaged_message) > 0:
            # Once we have a message, terminate
            return '<'+packaged_message[0]+'>'
        
    return ''


#def quick_listen(sock):
#    data = sock.recv(8192)
#    return data

