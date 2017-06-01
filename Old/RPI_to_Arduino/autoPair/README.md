# Automatic Pairing


## The issue

PyBluez [does not support pairing management](http://stackoverflow.com/questions/37500992/pybluez-pairing-bluetooth-device). Without pairing the HC-05, running `socket.connect((address, 1))` raises a `bluetooth.btcommon.BluetoothError: (111, 'Connection refused')` error. Currently, pairing is required manually using the desktop or `bluetoothctl` command line api. `bluetoothctl` can't easily be automated because it creates its own interactive prompt rather than running over command line flags.

## Possible solutions
- The [link above](http://stackoverflow.com/questions/37500992/pybluez-pairing-bluetooth-device) suggests implementing or at least looking for another command line tool to take care of this (it provides one for windows).
- [Here](http://stackoverflow.com/questions/42135297/setting-up-bluetooth-automatic-pairing-on-linux), implementing an application using 'BlueZ DBus API' is suggested and some useful links are provided.
- [This link](https://www.raspberrypi.org/forums/viewtopic.php?t=92695) also points to the same `simple-agent` [python script](https://github.com/hmallat/bluez5/blob/master/bluez5/test/simple-agent) which is included in the bluez source code (under a test directory).

### Using the simple-agent python script
After removing the HC-05 from the list of paired devices, I attempted to use the `simple-agent` python script to initiate the pairing request.
1. Copy `simple-agent` and its one dependency `bluezutils.py` into a directory
2. In one terminal run `python simple-agent`
3. In another, run a python script that uses `piduino.utils.connect` eg `piduino_example.py`
4. This hangs on 'Attempting to connect to device...'
5. In the original terminal, simple-agent requests a PIN. After entering the PIN, the device is paired without using bluetoothctl and `Connection refused` error isn't raised.

This suggestst that `simple-agent` can be adapted for automatic pairing.

### Adapting the simple-agent python script
1. The `bluezutils.py` script is not needed unless actively trying to pair with a device. It is only used when the script is called with arguments so my testing before didn't use it.
2. This [link](https://kernel.googlesource.com/pub/scm/bluetooth/bluez/+/5.16/doc/agent-api.txt) explains what each of the methods should do.
3. Changed KeyboardDisplay to DisplayYesNo according to [this](https://books.google.co.uk/books?id=-LMq0NhoEQgC&pg=PA218&lpg=PA218&dq=NoInputNoOutput+capability&source=bl&ots=AYuXvgODVw&sig=ghynBpB0WKNjXtBrnQqHO-abtLI&hl=en&sa=X&ved=0ahUKEwjb_oPNiK7TAhWMDcAKHU-QAHwQ6AEITjAG#v=onepage&q=NoInputNoOutput%20capability&f=false)

## Notes
### GUI compatibility
When using the python agent (or even bluetoothctl), there is still a GUI pairing request on the screen. E.g. 'Do you want to pair with this device (cancel) (yes)'.
- By doing **nothing** then the python agent handles the request successfully and the pairing works (although this message isn't dismissed)
- By **accepting** this pairing request then the device gets paired - this python script to supposed to remove this human interaction
- By **declining** this pairing request then the device is paired by the python script and (assuming responding to the GUI is slower than the script) then immediately unpaired.

### Bluetooth Error 11 Resource temporarily unavailable
I started getting this error during testing. I reverted back to 3ffa296fe0c3c8eb63dc4a85a5247ccc3cb1ce5e (when everything was working) and still got the error so it seemed to be something to do with the PI.
After doing some basic checks (is the arduino paired?) I still got the error.
I reflashed the raspberry pi with a clean image and the same error comes up.
After reveting to 3ffa296fe0c3c8eb63dc4a85a5247ccc3cb1ce5e again, everything works.
Created a branch to fix this: SocketBlocking


**Don't click cancel on the GUI pairing request**
