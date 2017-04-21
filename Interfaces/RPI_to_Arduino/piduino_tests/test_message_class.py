import pytest
import sys
sys.path.append('../piduino')
from piduino.piduino import Message
from piduino.piduino import check_valid
from piduino.piduino import Packet

def test_initialise_message_from_valid_components_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    mymessage = Message.from_components(source, destination, payload)
    assert mymessage.source == source
    assert mymessage.destination == destination
    assert mymessage.payload == payload
    

def test_initialise_message_from_valid_packet_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packaged = (Packet.START + source
                + Packet.DIVIDE + destination
                + Packet.DIVIDE + payload
                + Packet.END)
    mymessage = Message.from_packaged(packaged)
    assert mymessage.source == source
    assert mymessage.destination == destination
    assert mymessage.payload == payload

def test_initialise_message_from_invalid_packet_fails():
    packaged = ''
    with pytest.raises(IOError):
        mymessage = Message.from_packaged(packaged)

def test_package_message_runs():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    mymessage = Message.from_components(source, destination, payload)
    assert check_valid(mymessage.package()) == True

def test_package_is_inverse_of_unpackage():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packaged = (Packet.START + source
                + Packet.DIVIDE + destination
                + Packet.DIVIDE + payload
                + Packet.END)
    mymessage = Message.from_packaged(packaged)
    assert mymessage.package() == packaged
    
