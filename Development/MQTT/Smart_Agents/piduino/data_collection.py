# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 15:24:20 2017

@author: rbl46509
"""
import time
import threading
import piduino
import csv

def timestamp():
    # Returns an integer UNIX time
    return str(int(time.time()))
    
'''
ARDUINO THREADS:
    The threads below are called to handle the smart agents connections with its
    edge devices
'''
def handshake_protocol(device, timeout=5):
    '''
    Given a device, request a handshake. If handshake is completed,
    return the name of the device. Otherwise return None.
    '''
    # Clean out the buffers
    flag = device.flush()
    if flag:
        raise flag
    
    # Request a handshake
    flag = device.handshake_request()
    if flag:
        raise flag
        
    t0 = time.time()
    # Wait for a response
    while time.time() - t0 < timeout:
        if device.ready():
            flag, message = device.receive_json()
            if type(flag) == piduino.NotConnectedError:
                # The device has been disconnected!
                return None
            else:
                if message != '':
                    if message["topic"] == "handshake":
                        return message["payload"]
    return None
            
def connection_thread(device):
    '''
    Handles the connection to an edge device
    '''
    # handles the connection
    device.processing = True
    # Connect
    flag = device.connect()
    if flag:
        device.error = True
    else:
        
        # Wait (delay is needed before using the serial port)
        time.sleep(4)
    
        # Handshake
        name = handshake_protocol(device)
        if name == None:
            device.error = True
        else:
            device.name = name
            device.verified = True
            
    device.processing = False
    
    
connectedEdgeDevices = []
runningThreads = []
AGENTNAME = 'Coffee_Room'
try:
    while True:
        time.sleep(0.5)
        # Make connections to arduinos
        # Check for serial connections to suitable devices
        comports = piduino.comport_scan('Arduino')
            
        
        for comport in comports:
            # Check if we are already connected to this device
            if comport not in [d.comport for d in connectedEdgeDevices]:
                # If not, create a new device manager
                device = piduino.SerialDevice(comport)
                connectedEdgeDevices.append(device)
                
                # Spawn a new thread to handle the process of connection
                t = threading.Thread(name=comport, target=connection_thread, args=(device,))
                runningThreads.append(t)
                t.start()
        
        # Receive data
        for device in connectedEdgeDevices:
            if device.connected and device.verified:
                flag, waiting = device.ready()
                
                if type(flag) == piduino.NotConnectedError:
                    # The device has been disconnected! Remove it from our list of verified devices
                    try:
                        device.shutdown()
                    except:
                        pass
                    
                    # Flag the arduino as disconnected
                    device.error = True    
                    
                if waiting:
                    flag, message = device.receive_json()
                    if flag:
                        pass
                    else:
                        if message != '':
                            row = [timestamp(), str(message["payload"])]
                            with open('Data/' 
                                      + AGENTNAME 
                                      + '-' + str(device.name) 
                                      + '-' + message["topic"] + '.csv', 
                                      'a', newline='') as f:
                                writer = csv.writer(f)
                                writer.writerow(row)
                                
        # Clean disconnected arduinos out of the list
        connectedEdgeDevices = [d for d in connectedEdgeDevices if not d.error]

except Exception as e:
    raise e
finally:
    for device in connectedEdgeDevices:
        try:
            device.shutdown()
        except:
            pass
    