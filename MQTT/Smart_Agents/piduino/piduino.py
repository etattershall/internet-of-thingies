# -*- coding: utf-8 -*-
"""
Created on Wed May 24 14:20:25 2017


Notes: All functions return their errors, so error handling should be done by the
application

@author: Emma Tattershall
"""

import json
import serial
import serial.tools.list_ports
import time
import re

__version__ = '0.0.1'

class NotYetImplemented(Exception):
    def __init__(self, value):
        self.value = value

class NotConnected(Exception):
    def __init__(self, value):
        self.value = value
        
def comport_scan(device_type='Arduino'):
    # Returns a list of com ports connected to arduinos
    matching_ports = []
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.description.startswith(device_type):
            matching_ports.append(port.device)
    return matching_ports
    
    
class SerialDevice():
    '''
    The microcontroller should be constantly sending sensor readings. It does not 
    require input from the smart agent.
    '''
    def __init__(self, comport):
        self.name = None
        self.subscriptions = None
        self.comport = comport
        self.ser = None
        
    def connect(self, timeout=10):
        try:
            self.ser = serial.Serial(self.comport, 9600, timeout=timeout)
            return None
        except Exception as e:
            return e
    
    def fileno(self):
        if ser != None:
            return ser.fileno()
        else:
            raise NotConnected("Need to connect first!")
            
    def send(self, message):
        packet = json.dumps(message).encode('ascii')
        try:
            self.ser.write(packet)
            return None
        except Exception as e:
            return e
            
    def receive(self, timeout=10):
        '''
        Receives a single message from a device, unless timeout is reached first 
        '''
        t0 = time.time()
        data = ''
        while True:
            # We read one byte at a time.
            data += self.ser.read().decode(errors='ignore')
            # Note: this program cannot cope with internal '{}' brackets inside the json, so be sure not
            # to use them in the plaintext when composing a message!
            potential_messages = re.findall('\{[^\{\}]+\}', data)
            for potential_message in potential_messages:
                try:
                    message = json.loads(potential_message)
                    # json loads is a bit of a blunt instrument. It will interpret "hi" as a 
                    # jsonic object! 
                    if type(message) == dict:
                        return message

                except Exception as e:
                    # Exceptions occur when the message is incomplete. Therefore we
                    # can ignore them!
                    pass
                
            if time.time() - t0 > timeout:
                return []
        

if __name__ == '__main__':
    pass