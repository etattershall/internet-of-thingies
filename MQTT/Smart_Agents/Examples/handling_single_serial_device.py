# -*- coding: utf-8 -*-
"""
Created on Wed May 24 15:06:06 2017

@author: Emma Tattershall
"""
import sys
import time

try:
    from ..piduino import piduino
except SystemError:
    sys.path.append('../piduino')
    import piduino
    
comports = piduino.comport_scan('Arduino')

for comport in comports:
    arduino = piduino.SerialDevice(comport=comport)
    
    # Connect
    flag = arduino.connect()
    if flag:
        raise flag
    
    # The arduino will need a few seconds to adjust to the connection
    time.sleep(4)
    
    # Receive data
    while True:
        message = arduino.receive()
        if flag:
            raise flag
        else:
            print(message)
            #if message["type"] == "pub":
            #    publish.single('arduino/' + message["topic"], message["payload"])