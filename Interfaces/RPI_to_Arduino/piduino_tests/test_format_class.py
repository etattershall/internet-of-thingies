import sys
sys.path.append('../piduino')
from piduino.piduino import Format

def test_chosen_packet_constants_are_not_forbidden():
    assert Format().check_constants() == True

def test_valid_packet_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.DIVIDE + payload +
                        Format.END)
                        
    assert Format().contains_packet(packet) == True

def test_empty_string_fails():
    packet = ''
    assert Format().contains_packet(packet) == False
    
def test_packet_with_too_few_components_fails():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.END)
                        
    assert Format().contains_packet(packet) == False

def test_incomplete_packet_fails():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.DIVIDE + payload)
                        
    assert Format().contains_packet(packet) == False
    
def test_packet_with_too_many_components_fails():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.DIVIDE + payload +
                        Format.DIVIDE + payload +
                        Format.END)
                        
    assert Format().contains_packet(packet) == True
    
def test_double_packet_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.DIVIDE + payload +
                        Format.END)*2
        
    assert Format().contains_packet(packet) == True    

def test_unescape_empty_string():
    assert Format().unescape("") == ""

def test_unescape_escaped_string():
    assert Format().unescape(Format.ESCAPE+Format.END+"Hello") == Format.END + "Hello"

def test_unescape_double_escaped_string():
    assert Format().unescape(2*(Format.ESCAPE+Format.END)+"Hello") == 2*Format.END + "Hello"

def test_unescape_escaped_escape():
    assert Format().unescape(Format.ESCAPE+Format.ESCAPE+"Hello") == Format.ESCAPE + "Hello"

