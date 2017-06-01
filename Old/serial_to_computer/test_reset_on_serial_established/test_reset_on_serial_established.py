'''Test whether the arduino resets when a python serial interface is
established.

Should be used with test_reset_serial_established.ino

Result:
    - 'Settings things up!' is recieved every time the python script is run, in
    the same way as in the arduino IDE
    - The inital characters from before the reset are also recieved

'''

import serial
import serial.tools.list_ports


def getFirstArduinoPort():
    "Returns the port (eg COM5) of the first arduino"
    ports = serial.tools.list_ports.comports()
    for p in ports:
        # Check to see if the serial port is connected to an Arduino
        if 'Arduino' in p.description:
            # Return this port
            return p.device
    raise IOError("No Arduino found!")


def runTest(baudRate, repeats, lines):
    """Opens the serial port at a 'baudRate', prints 'lines' lines repeated
    'repeats' times."""
    print(" ----- Start @ {} -----".format(baudRate))
    for i in range(repeats):
        print(" -- Repeat {}".format(i + 1))
        with serial.Serial(getFirstArduinoPort(), baudRate) as ser:
            for linesPrinted in range(lines):
                print(ser.readline())
        print(" ----- End -----")


runTest(115200, 5, 20)
