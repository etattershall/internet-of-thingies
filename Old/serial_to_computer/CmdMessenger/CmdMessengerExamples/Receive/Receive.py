'''Python program to interface with the 'receive' example from CmdMessenger.

On the Arduino side, it demonstrates how to:
  - Define commands
  - Set up a serial connection
  - Receive a command with a parameter from the PC
On the PC side, it demonstrates how to:
  - Define commands
  - Set up a serial connection
  - Send a command with a parameter to the Arduino
'''

import PyCmdMessenger
import time


# Create an arduino board instance on port 'COM5' with the same baud_rate
# as in Receive.ino
arduino = PyCmdMessenger.ArduinoBoard("COM5", baud_rate=115200)

# Create a list of command, argument type pairs
# In this case, kSetLed takes one bool argument: True to turn it on, False
# to turn it off.
commands = [["kSetLed", "?"]]

# Initialise the messenger
c = PyCmdMessenger.CmdMessenger(arduino, commands)


def runExample():
    # store current led state
    ledState = True
    while True:
        # Forever...
        c.send(commands[0][0], ledState)
        ledState = not ledState
        print("Led On" if ledState else "Led Off")
        time.sleep(1)


if __name__ == "__main__":
    runExample()
