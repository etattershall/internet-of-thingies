import pytest
import sys
sys.path.append('../piduino')
from piduino.piduino import Message
from piduino.piduino import Format

def test_message_initialise_from_valid_components_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    mymessage = Message([source, destination, payload])
    assert mymessage.source == source
    assert mymessage.destination == destination
    assert mymessage.payload == payload
    
def test_message_components_inverse_of_init():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    mymessage = Message([source, destination, payload])
    assert mymessage.components() == [source, destination, payload]




