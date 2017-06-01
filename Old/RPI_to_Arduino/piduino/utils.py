from __future__ import print_function, absolute_import, division

import os
import sys
import re
import warnings
import socket, struct
import time


try:
    import bluetooth
    import bluetooth._bluetooth as _bt
except ImportError:
    warnings.warn("Bluetooth can't be imported, this must be testing...")

# Define special characters
PACKET_START = "<"
PACKET_DIVIDE = "|"
PACKET_END = ">"
ESCAPE = "\\"

# A list of characters to escape
TO_ESCAPE = [PACKET_START, PACKET_DIVIDE, PACKET_END, ESCAPE]


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
    if not bluetooth.is_valid_address(source):
        raise IOError("Source address formatted incorrectly")
    if not bluetooth.is_valid_address(destination):
        raise IOError("Destination address formatted incorrectly")

    escaped = tuple(escape(item) for item in [source, destination, message])
    eSource, eDesination, eMessage = escaped

    if len(eMessage) > MAX_LENGTH:
        raise IOError("Escaped message greater than max message length")

    return '<' + eSource + '|' + eDesination + '|' + eMessage + '>'


def unpackage(packaged_message):
    """
    Takes a packaged message in the form
    '<source|destination|message>'
    and returns the separate components, unescaped

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
    if(not packaged_message.startswith(PACKET_START) or
       not packaged_message.endswith(PACKET_END)):
        raise IOError("Invalid message: not bookended with "
                      "'{}{}'".format(PACKET_START, PACKET_END))
    # A list [source, destination, message] to store the packet as it is parsed
    # char by char
    packetData = [""]
    charIsEscaped = False
    for currentChar in packaged_message[1:-1]:  # remove start and end
        # If this character is splitting sections of the packet, start a new
        # section
        if currentChar == PACKET_DIVIDE and not charIsEscaped:
            packetData.append("")
            continue  # Don't look at this character any more

        # Add this character to the current section of the packet
        if (currentChar == ESCAPE and charIsEscaped) or currentChar != ESCAPE:
            packetData[-1] += currentChar

        # Set escape flag for next character
        charIsEscaped = currentChar == ESCAPE and not charIsEscaped

    if len(packetData) != 3:
        raise IOError("Invalid message: wrong number of components")

    return tuple(packetData)


def send_message(sock, packaged_message):
    """
    Takes a packaged message in the form
    '<source|destination|message>'
    and sends it to the socket

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
        data += sock.recv(1024)
        packaged_message = ""  # Will store a raw message "<..|..|..>"
        charIsEscaped = False
        # Set to true on PACKET_START upto PACKET_END
        insidePacket = False
        # Step through each character one at a time
        for currentChar in data:
            # If this is the start of the packet, set the flag to store it
            if currentChar == PACKET_START and not charIsEscaped:
                insidePacket = True

            # Check only escaped characters are escaped
            if charIsEscaped:
                if currentChar not in TO_ESCAPE:
                    warnings.warn("Wrongly escaped character")

            # Add this character if in the packet
            if insidePacket:
                packaged_message += currentChar


            # Deal with the end of the packet
            if currentChar == PACKET_END and not charIsEscaped:
                insidePacket = False
                return packaged_message
              
            # Set up the charIsEscaped flag for the next char
            charIsEscaped = currentChar == ESCAPE and not charIsEscaped

    return ""


def escape(text):
    """
    Escapes the special characters from a string

    Parameters
    ----------
    text: str
        string to be escaped

    Returns
    -------
    str
        escaped string

    Notes
    -----
    Could be done completely with regex, something like:
        regex = r"([" + r"".join(re.escape(char) for char in TO_ESCAPE) + r"])"
        return re.sub(regex, re.escape(ESCAPE) + r"\1", text)
    But:
        1) May cause issues if TO_ESCAPE contains a regex character eg "]"
        2) Wouldn't work if we wanted to send bytes rather than strings later?
        3) Arudino doesn't have re library so easier to ensure that method
           is same (copy the code, change the syntax).
    """

    currentIndex = 0
    while currentIndex < len(text):
        # Go through one character at a time
        if text[currentIndex] in TO_ESCAPE:
            # If this char needs escaping, add an escape before it.
            # text:            "aad\asdf"
            # current index:       ^
            # new text:        "add\\asdf"
            # updated index:        ^
            text = text[:currentIndex] + ESCAPE + text[currentIndex:]
            currentIndex += 1  # Update the index
        currentIndex += 1
    return text
