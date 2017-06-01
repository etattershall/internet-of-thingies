# CmdMessenger
https://github.com/thijse/Arduino-CmdMessenger

A library to send and recieve commands / arguments over serial. It can read all primary data types.

On the PC side, use this [python library](https://github.com/harmsm/PyCmdMessenger).

Investigating for a better way to communicate over serial.

## Installation
1. CmdMessenger: [The Arduino Library Manager](http://www.arduino.cc/en/guide/libraries#toc3)
2. PyCmdMessenger: pip `pip3 install PyCmdMessenger`

## Usage Reference

```Python
import PyCmdMessenger

# Initialize an ArduinoBoard instance.  This is where you specify baud rate and
# serial timeout.  If you are using a non ATmega328 board, you might also need
# to set the data sizes (bytes for integers, longs, floats, and doubles).  
arduino = PyCmdMessenger.ArduinoBoard("/dev/ttyACM0",baud_rate=9600)

# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [["who_are_you",""],
            ["my_name_is","s"],
            ["sum_two_ints","ii"],
            ["sum_is","i"],
            ["error","s"]]

# Initialize the messenger
c = PyCmdMessenger.CmdMessenger(arduino,commands)

# Send
c.send("who_are_you")
# Receive. Should give ["my_name_is",["Bob"],TIME_RECIEVED]
msg = c.receive()
print(msg)

# Send with multiple parameters
c.send("sum_two_ints",4,1)
msg = c.receive()

# should give ["sum_is",[5],TIME_RECEIVED]
print(msg)
```

## Format arguments

The format for each argument sent with a command (or received with a command)
is determined by the command_formats list passed to the CmdMessenger class (see
example above). Alternatively, it can be specified by the keyword arg_formats
passed directly to the `send` or `receive` methods.  The format specification
is in the table below.  If a given command returns a single float value, the
format string for that command would be `"f"`.  If it returns five floats, the
format string would be `"fffff"`.  The types can be mixed and matched at will.
`"si??f"` would specify a command that sends or receives five arguments that are
a string, integer, bool, bool, and float.  If no argument is associated with a
command, an empty string (`""`) or `None` can be used for the format.

### Format reference table

| format | arduino type  | Python Type              | Arduino receive                                       | Arduino send                        |
|--------|---------------|--------------------------|-------------------------------------------------------|-------------------------------------|
| "i"    | int           | int                      | `int value = c.readBinArg<int>();`                    | `c.sendBinCmd(COMMAND_NAME,value);` |
| "b"    | byte          | int                      | `int value = c.readBinArg<byte>();`                   | `c.sendBinCmd(COMMAND_NAME,value);` |
| "I"    | unsigned int  | int                      | `unsigned int value = c.readBinArg<unsigned int>();`  | `c.sendBinCmd(COMMAND_NAME,value);` |
| "l"    | long          | int                      | `long value = c.readBinArg<long>();`                  | `c.sendBinCmd(COMMAND_NAME,value);` |
| "L"    | unsigned long | int                      | `unsigned long value = c.readBinArg<unsigned long>();`| `c.sendBinCmd(COMMAND_NAME,value);` |
| "f"    | float         | float                    | `float value = c.readBinArg<float>();`                | `c.sendBinCmd(COMMAND_NAME,value);` |
| "d"    | double        | float                    | `double value = c.readBinArg<double>();`              | `c.sendBinCmd(COMMAND_NAME,value);` |
| "?"    | bool          | bool                     | `bool value = c.readBinArg<bool>();`                  | `c.sendBinCmd(COMMAND_NAME,value);` |
| "c"    | char          | str or bytes, length = 1 | `char value = c.readBinArg<char>();`                  | `c.sendBinCmd(COMMAND_NAME,value);` |
| "s"    | char[]        | str or bytes             | `char value[SIZE] = c.readStringArg();`               | `c.sendCmd(COMMAND_NAME,value);`    |

PyCmdMessenger takes care of type conversion before anything is sent over the
serial connection.  For example, if the user sends an integer as an `"f"`
(float), PyCmdMessenger will run `float(value)` in python before passing it.
It will warn the user for destructive conversions (say, a float to an
integer).  It will throw a `ValueError` if the conversion cannot be done (e.g.
the string 'ABC' to integer).  It will throw an `OverflowError` if the passed
value cannot be accomodated in the specififed arduino data type (say, by
passing an integer greater than 32767 to a 2-byte integer, or a negative number
to an unsigned int).  The sizes for each arduino type are determined by the
`XXX_bytes` attributes of the ArduinoBoard class.

### Special formats
`"*"` tells the CmdMessenger class to repeat the previous format for all
remaining arguments, however many there are. This is useful if your arduino
function sends back an undetermined number of arguments of the same type,
for example.  There are a few rules for use:

   + Only one `*` may be specified per format string.
   + The one `*` must occur *last*
   + It must be preceded by a different format that will then be repeated.

   Examples:
   + `"i*"` will use an integer format until it runs out of fields.
   + `"fs?*"` will read/send the first two fields as a `float` and `string`,
     then any remaining fields as `bool`.
