# -*- coding: utf-8 -*-
"""
Created on Wed May 24 14:20:25 2017


Notes: All functions return their errors, so error handling should be done by the
application

@author: Emma Tattershall
"""

import json
import serial
from serial import SerialException
import serial.tools.list_ports
import time
import re
import sys

__version__ = '0.0.1'

class NotYetImplemented(Exception):
    def __init__(self, value):
        self.value = value


class AuthenticationError(Exception):
    def __init__(self, value):
        self.value = value

class ReadTimeoutError(Exception):
    def __init__(self, value):
        self.value = value
     
class NotConnectedError(Exception):
    def __init__(self, value):
        self.value = value
        
def comport_scan(device_type='Arduino'):
    # Returns a list of com ports connected to arduinos
    matching_ports = []
    if sys.platform.startswith('win'):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.description.startswith(device_type):
                matching_ports.append(port.device)
    elif sys.platform.startswith('linux'):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            matching_ports.append(port[0])
    return matching_ports
    
    
class SerialDevice():
    '''
    The microcontroller should be constantly sending sensor readings. It does not 
    require input from the smart agent.
    '''
    def __init__(self, comport):
        self.name = None
        self.comport = comport
        self.ser = None
        self.topics = set()
        self.connected = False
        self.verified = False
        self.processing = False
        self.error = False
        
    def connect(self, timeout=10):
        try:
            self.ser = serial.Serial(self.comport, 9600, timeout=timeout)
            self.connected = True
            if not sys.platform.startswith('win'):
                self.ser.nonblocking()
            return None
        except Exception as e:
            return e
        
    def send(self, message):
        packet = json.dumps(message).encode('ascii')
        try:
            self.ser.write(packet)
            return None
        except Exception as e:
            return e
            
    def receive_json(self, timeout=10):
        '''
        Receives a single message from a device, unless timeout is reached first 
        '''
        t0 = time.time()
        data = ''
        while True:
            # We read one byte at a time.
            try:
                data += self.ser.read().decode(errors='ignore')
            except SerialException as e:
                return NotConnectedError("The device is not connected"), ''
            # Note: this program cannot cope with internal '{}' brackets inside the json, so be sure not
            # to use them in the plaintext when composing a message!
            potential_messages = re.findall('\{[^\{\}]+\}', data)
            for potential_message in potential_messages:
                try:
                    message = json.loads(potential_message)
                    # json loads is a bit of a blunt instrument. It will interpret "hi" as a 
                    # jsonic object! 
                    if type(message) == dict:
                        return None, message

                except Exception as e:
                    # Exceptions occur when the message is incomplete. Therefore we
                    # can ignore them!
                    pass
                
            if time.time() - t0 > timeout:
                return ReadTimeoutError("The timeout was reached before a valid message was read"), ''

    def receive_string(self, timeout=10):
        '''
        Receives a string
        '''
        data = ''
        while self.ser.in_waiting:
            data += self.ser.read().decode(errors='ignore')
        return data
    
    def ready(self):
        '''
        Check if the device is ready to send
        '''
        try:
            if serial.VERSION.startswith('2'):
                if self.ser.inWaiting() > 0:
                    return None, True
                else:
                    return None, False
            else:
                if self.ser.in_waiting > 0:
                    return None, True
                else:
                    return None, False     
        except SerialException as e:
            return NotConnectedError("The device is not connected"), False
            
    def handshake_request(self):
        '''
        Can be sent at any time by the smart agent to the arduino. 
        If the arduino receives it, it should respond with a message in the
        format:
            {
                 'topic': 'handshake',
                 'source': Arduino ID number,
                 'payload': 'Hello'
            }
        '''
        message = {
        'topic': 'handshake', 
        'payload': 'Hello'
        }
        return self.send(message)
        
    def flush(self):
        '''
        Flushes the serial buffer
        '''
        try:
            self.ser.flushInput()
            self.ser.flushOutput()
            return None
        except Exception as e:
            return e

    def shutdown(self):
        try:
            self.ser.close()
            return None
        except Exception as e:
            return e
        

if __name__ == '__main__':
    pass
