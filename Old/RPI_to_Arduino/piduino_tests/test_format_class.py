import sys
sys.path.append('../piduino')
from piduino.piduino import Format

def test_format_find_packets_valid_packet_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.DIVIDE + payload +
                        Format.END)                
    assert len(Format().find_packets(packet)) == 1

def test_format_find_packets_empty_string_fails():
    packet = ''
    assert len(Format().find_packets(packet)) == 0
    
def test_format_find_packets_packet_with_too_few_components_fails():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.END)
                        
    assert len(Format().find_packets(packet)) == 0

def test_format_find_packets_incomplete_packet_fails():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.DIVIDE + payload)
                        
    assert len(Format().find_packets(packet)) == 0
    
def test_format_find_packets_packet_with_too_many_components_fails():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.DIVIDE + payload +
                        Format.DIVIDE + payload +
                        Format.END)      
    assert len(Format().find_packets(packet)) == 0
    
def test_format_find_packets_double_packet_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.DIVIDE + payload +
                        Format.END)*2
        
    assert len(Format().find_packets(packet)) == 2

def test_format_find_packets_escaped_packet_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = Format.ESCAPE+Format.START+'Hello World!'
    packet = (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.DIVIDE + payload +
                        Format.END)
        
    assert len(Format().find_packets(packet)) == 1

def test_format_package_normal_string_passes():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    components = [source, destination, payload]
    assert Format().package(components) == (Format.START + source +
                        Format.DIVIDE + destination +
                        Format.DIVIDE + payload +
                        Format.END)

def test_format_package_inverse_of_find_package_normal():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = 'Hello World!'
    components = [source, destination, payload]
    packet = Format().package(components)
    assert Format().find_packets(packet)[0] == components

def test_format_package_inverse_of_find_package_escaping():
    source = '00:00:00:00:00:00'
    destination = '11:11:11:11:11:11'
    payload = Format.DIVIDE + Format.ESCAPE + Format.START
    components = [source, destination, payload]
    packet = Format().package(components)
    assert Format().find_packets(packet)[0] == components
    
def test_format_unescape_escaped_string():
    assert Format()._Format__unescape(Format.ESCAPE+Format.END+"Hello") == Format.END + "Hello"

def test_format_unescape_double_escaped_string():
    assert Format()._Format__unescape(2*(Format.ESCAPE+Format.END)+"Hello") == 2*Format.END + "Hello"

def test_format_unescape_escaped_escape():
    assert Format()._Format__unescape(Format.ESCAPE+Format.ESCAPE+"Hello") == Format.ESCAPE + "Hello"

def test_format_escape_empty_string():
    assert Format()._Format__escape("") == ""
    
def test_format_escape_string_with_no_reserved_characters():
    assert Format()._Format__escape("Hello, World!") == "Hello, World!"

def test_format_escape_escape():
    assert Format()._Format__escape(Format.ESCAPE) == 2*Format.ESCAPE
    
def test_format_escape_string_with_reserved_characters():
    assert Format()._Format__escape(Format.ESCAPE + Format.START + "Hello"
                           + Format.END + Format.DIVIDE) == \
           (Format.ESCAPE + Format.ESCAPE + Format.ESCAPE + Format.START
            + "Hello" + Format.ESCAPE + Format.END + Format.ESCAPE + Format.DIVIDE)

def test_format_unescape_inverse_of_escape():
    dodgy_string = Format.ESCAPE + Format.START + "Hello" + Format.END + Format.DIVIDE
    assert Format()._Format__unescape(Format()._Format__escape(dodgy_string)) == dodgy_string
