# Open WRT on BT HomeHub 2.0 Type A

[The main OpenWRT Tutorial for this router](https://wiki.openwrt.org/toh/bt/homehub_v2a#flashing_the_new_bootloader)

## Model
The hub that we have is a Type A as it says so on the back and has a broadcom chip inside.

The revision is `rev.2` according to the pictures [here](https://wiki.openwrt.org/toh/bt/homehub_v2a#flashing_the_new_bootloader) (note the LHS).

## JTAG method
This is the 'tried and tested approach' to get a custom CFE. There is another method using USB but I am reluctant to try until knowing BT firmware version.

### What is JTAG?

[Wikipedia](https://en.wikipedia.org/wiki/JTAG) and [OpenWRT](https://wiki.openwrt.org/doc/hardware/port.jtag) describe it as an interface to test integrated circuits. Importantly, you can use it to write to the Flash Chip.

### Taking the HomeHub apart

1. Remove two screws from bottom.
2. Split the two plastic sections apart.
3. Remove screw holding phone power cables to the front section
4. Remove three screws from the PCB
4. Remove PCB from the back section

### Wiring the PI
The method uses [this library](https://github.com/oxplot/tjtag-pi) to use the raspberry as a JTAG interface device.

This is the wiring diagram from the library:

![Wiring Diagram](https://raw.githubusercontent.com/oxplot/tjtag-pi/master/wiring.jpg)

Note that the pinout of the device on the right is different to the BT Home Hub. See the labeled diagram below and match the pin names.

![BT HomeHub wiring diagram](https://wiki.openwrt.org/_media/media/bt/homehub2a_rev2_jtag.jpg?cache=)

### Running tjtag-pi

Following the instructions from the library's README:
1. Wired up the pi as above
2. Powered up WRT (5 blue lights then settled to just 'power')
3. Checkout, compile and run code as in their README (running the last command as root with `sudo` because it couldn't access `/dev/mem`):

    ```bash
    $ cd ~
    $ git clone git@github.com:oxplot/tjtag-pi.git
    $ cd tjtag-pi
    $ make pi
    $ sudo ./tjtag -probeonly
    ```
4. After this failed, attempt with `/noemw`
5. This also failed to recognise the device.
