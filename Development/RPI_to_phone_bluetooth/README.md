# RPI to Phone (or computer probably)

## Initial Setup

1. First tell the 'sdp server' that the raspberry pi can provide a bluetooth serial port. To make sure that this happens every time that bluetooth is loaded, edit the `systemctl` service file for bluetooth to add the line `sdptool add SP` (SP for Serial Port). In the previous line, start `bluetoothd` with the `-C` flag for compatibility. This enables the command `sdptool`.

    ``` bash
    # Save the file as a variable rather than writing it out each time
    file=/lib/systemd/system/bluetooth.service
    # Create a backup just in case...
    sudo cp $file $file.backup
    # Add the -C option to the line stating with 'ExecStart='
    # Add the sdp tool command to a new line imediately after
    sudo sed -e "/^ExecStart=/ s/$/ -C/;/^ExecStart=/a ExecStartPost=/usr/bin/sdptool add SP" -i $file
    # Make systemctl read the edited file and restart bluetooth
    sudo systemctl daemon-reload
    sudo systemctl restart bluetooth

    # To check:
    sudo sdptool browse local  # should show 'Serial Port'
    ```
2. Use the command `bluetoothctl` to enter a bluetooth prompt `[bluetooth]#` (type `help` for a list of avaliable commands)
3. Setup bluetooth and pair with your device `XX:XX:XX:XX:XX:XX` (it must be visible)
    ```
    [bluetooth]# power on
    [bluetooth]# scan on
    [bluetooth]# pair XX:XX:XX:XX:XX:XX
    [bluetooth]# quit
    ```

## Setup every time
1. Setup bluetooth over serial `sudo rfcomm watch /dev/rfcomm0`
2. Connect bluetooth terminal (should see following output on the PI)
    ```
    pi@raspberry:~ $ sudo rfcomm watch /dev/rfcomm0
    Waiting for connection on channel 1
    Connection from XX:XX:XX:XX:XX:XX to /dev/rfcomm0
    Press CTRL-C for hangup
    ```
3. Switch to a different terminal and write / read from the file at `/dev/rfcomm0` for serial communication

## Example

### Sending the numbers 1 -> 5 over serial.

``` bash
for i in $(seq 5); do echo $i > /dev/rfcomm0; done
```

### Reading from serial
``` bash
cat /dev/rfcomm0
```
