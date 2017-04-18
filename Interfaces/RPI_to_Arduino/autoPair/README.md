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
