import sys
sys.path.append('../piduino')
from piduino.piduino import check_constants
from piduino.piduino import check_valid
from piduino.piduino import Packet

def test_chosen_packet_constants_are_not_forbidden():
    assert check_constants() == True

def test_valid_packet_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packaged_message = (Packet.START + source +
                        Packet.DIVIDE + destination +
                        Packet.DIVIDE + payload +
                        Packet.END)
                        
    assert check_valid(packaged_message) == True

def test_empty_string_fails():
    packaged_message = ''
    assert check_valid(packaged_message) == False
    
def test_packet_with_too_few_components_fails():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    packaged_message = (Packet.START + source +
                        Packet.DIVIDE + destination +
                        Packet.END)
                        
    assert check_valid(packaged_message) == False

def test_incomplete_packet_fails():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packaged_message = (Packet.START + source +
                        Packet.DIVIDE + destination +
                        Packet.DIVIDE + payload)
                        
    assert check_valid(packaged_message) == False
    
def test_packet_with_too_many_components_fails():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packaged_message = (Packet.START + source +
                        Packet.DIVIDE + destination +
                        Packet.DIVIDE + payload +
                        Packet.DIVIDE + payload +
                        Packet.END)
                        
    assert check_valid(packaged_message) == True
    
def test_double_packet_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packaged_message = (Packet.START + source +
                        Packet.DIVIDE + destination +
                        Packet.DIVIDE + payload +
                        Packet.END)*2
        
    assert check_valid(packaged_message) == True    
