'''
Tests that the autoPair.py script works to pair with the device. The device
should not be paired already.

To unpair:
bluetoothctl
remove XX:XX:XX:XX:XX:XX
'''

from piduino import utils
from time import sleep
import bluetooth.btcommon
import subprocess

def getArduinoDestination():
    '''Returns the destination for an arduino'''
    print("Scanning for arduinos")
    destinations = utils.scan('SCD_ARDUINO')
    if len(destinations) == 0:
        raise IOError('No Arduinos found!')
    else:
        destination = destinations[0]
    return destination


def connectWorks(destination):
    '''Tests that the PI can connect to destination
    destination:
    BT_Address
    '''
    print('Attempting to connect to device at ' + destination)
    try:
        socket = utils.connect(destination)
    except bluetooth.btcommon.BluetoothError as e:
        return False
    else:
        return True

def run():
    """Runs the test"""
    destination = getArduinoDestination()
    if connectWorks(destination):
        # If you thnk the device is already paired, there 
        # could be a rogue agent still running (and accepting)
        # the connection request, to check what agents are already
        # running run:
        # ps -x | grep autoPair.py | grep -v "grep"
        raise Exception("Unpair the device before this test!")
                        
        return
    else:
        print("The device isn't paired, starting the agent background script")
    try:
        # Start the deamon
        p = subprocess.Popen(["python", "piduino/autoPair.py"])
        print("Crudely waiting 10 seconds for the agent to start. Look out "
              "for 'Agent registered' being printed.")
        sleep(10)
        if connectWorks(destination):
            print("Passed: connect worked after starting the agent in the "
                  "background. The device is now paired")
        else:
            print("Failed: connect failed after starting the agent in the "
                  "background. The device did not get paired.")
    finally:
        # End the deamon
        p.kill()
        

if __name__ == "__main__":
    run()
