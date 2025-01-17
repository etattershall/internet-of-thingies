# Copied from
# https://github.com/harmsm/PyCmdMessenger/blob/master/examples/python-basic.py
# ------------------------------------------------------------------------------
# Python program using the library to interface with the arduino sketch above.
# ------------------------------------------------------------------------------

import PyCmdMessenger

# Initialize an ArduinoBoard instance.  This is where you specify baud rate and
# serial timeout.  If you are using a non ATmega328 board, you might also need
# to set the data sizes (bytes for integers, longs, floats, and doubles).
arduino = PyCmdMessenger.ArduinoBoard("COM" + input("COM<what?>"),
                                      baud_rate=9600)

# List of commands and their associated argument formats. These must be in the
# same order as in the sketch.
commands = [["who_are_you", ""],
            ["my_name_is", "s"],
            ["sum_two_ints", "ii"],
            ["sum_is", "i"],
            ["error", "s"]]

# Initialize the messenger
c = PyCmdMessenger.CmdMessenger(arduino, commands)

# Send
c.send("who_are_you")
# Receive. Should give ["my_name_is",["Bob"],TIME_RECIEVED]
msg = c.receive()
print(msg)

# Send with multiple parameters
c.send("sum_two_ints", 4, 1)
msg = c.receive()
# should give ["sum_is",[5],TIME_RECEIVED]
print(msg)


# Send an error - arduino doesn't have a callback for this...
c.send("sum_is", 2)
msg = c.receive()
print(msg)
