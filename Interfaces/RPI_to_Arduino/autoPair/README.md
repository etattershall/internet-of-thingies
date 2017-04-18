# Automatic Pairing


## The issue

PyBluez [does not support pairing management](http://stackoverflow.com/questions/37500992/pybluez-pairing-bluetooth-device). Without pairing the HC-05, running `socket.connect((address, 1))` raises a `bluetooth.btcommon.BluetoothError: (111, 'Connection refused')` error. Currently, pairing is required manually using the desktop or `bluetoothctl` command line api. `bluetoothctl` can't easily be automated because it creates its own interactive prompt rather than running over command line flags.

## Possible solutions
- The [link above](http://stackoverflow.com/questions/37500992/pybluez-pairing-bluetooth-device) suggests implementing or at least looking for another command line tool to take care of this (it provides one for windows).
- [Here](http://stackoverflow.com/questions/42135297/setting-up-bluetooth-automatic-pairing-on-linux), implementing an application using 'BlueZ DBus API' is suggested and some useful links are provided.

### Automate bluetoothctl
Commands can be sent to `bluetoothctl` through standard input.
```bash
bluetoothctl << EOF
power off
quit
EOF
```
Theoretically something like:
```bash
# Get BT address of first device with name "H-C"
addr=$(hcitoolcan | grep "H-C" | cut -f 2 | head -n 1)
bluetoothctl << EOF
pair $addr
PIN HERE
EOF
```
But this doesn't work because pairing takes time
