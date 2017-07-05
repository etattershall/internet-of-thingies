
# Bridging LAN over bluetooth

## What is bridging

Joining two interfaces (eg `eth0` and `wlan0`) to the same network. This might be a way to join bluetooth to the rest of the internet. See [this page](https://wiki.debian.org/BridgeNetworkConnections) for more information.

### Installing
bridge-utils provides the tools to setup a bridge. Install this with `sudo apt install bridge-utils`.

This gives access to the `brctl` command line tool.

[`brctl` cmds](https://wiki.debian.org/BridgeNetworkConnections)

### Library

For the moment, a python script `bt-pan` configures either end of the bluetooth setup. It is included in a library of misc tools `git clone https://github.com/mk-fg/fgtk.git`. The script's license allows it to be included here to avoid this step.

[bt-pan and general info for Bluez5](http://blog.fraggod.net/2015/03/28/bluetooth-pan-network-setup-with-bluez-5x.html)


### Setup

#### Standard Bluetooth Setup

Pair **and trust** the two devices using any of the standard methods.

#### Changes to networking

It appears that our current networking solution (`dhcpcd.conf`) isn't designed to setup bridge interfaces.
There are many resources that show how to setup persistant bridge interfaces using `/etc/network/interfaces`. However, this seems to be legacy and there is a message talking about conflicts between `/etc/network/interfaces` and `dhcpcd.conf`.

Instead, another option seems to be using systemd to configure the networking.

- [There is a guide here](https://major.io/2015/03/26/creating-a-bridge-for-virtual-machines-using-systemd-networkd)

- [Notes mainly from this site](https://www.linux.com/learn/understanding-and-using-systemd)
- [..And the blind blog](https://blind.guru/tag/bluetooth-pan.html)

systemd can be used to setup the bridge from every boot so you always access the internet through `br0` rather than choosing between `eth0` or `bnep0` (bluetooth).

This only worked if I set the static ip address/ gateway using systemd rather than `dhcpcd.conf`. I couldn't get the DNS part of systemd to work so the standard method (`dhcpcd.conf`) is still used for that.

First remove `eth0` completely from dhcpcd.conf (we don't want eth0 to have an ip address) and set `br0` to (note the removal of ip_address and gateway):

```
interface br0
static domain_name_servers=130.246.8.13
```

Enable `systemd-networkd` and setup the network over `systemd` using `pan.network`, `br0.netdev` and `br0.network`.

**Replace `[PUT YOUR IP ADDRESS HERE]` with your ip address**

```bash
sudo systemctl enable systemd-networkd
sudo cp pan-eth0.network /etc/systemd/network/
sudo cp pan-bnep0.network /etc/systemd/network/
sudo cp br0.netdev /etc/systemd/network/
sudo sed -i "s/IP_ADDRESS_HERE/[PUT YOUR IP ADDRESS HERE]" br0.network
sudo cp br0.network /etc/systemd/network/
```
And reboot!

#### python-systemd

The python module `systemd` is required to run `bt-pan`. I couldn't get the python2 version to install (bt-pan is written in python2). Instead, I installed the python3 version using `sudo apt install python3-systemd` and converted `bt-pan` to python3 (see this directory).


#### Starting bluetooth pan server/ client from systemd

##### Server Side

The `bt-pan` server can be run as a systemd service so that it is running from boot. To do this:
```bash
sudo cp pan.service /etc/systemd/system/
sudo systemctl enable pan.service
```

- To check the status `sudo systemctl status pan`
- To stop/start/restart: `sudo systemctl stop/start/restart pan`


##### Client Side
Setup as above but this service is simpler (although you can pass the bt address as an argument).
```bash
sudo cp pan@.service /etc/systemd/system/
# Start by specifying BT address...
systemctl start pan@B8:27:EB:96:85:A1
```
This will need to be run after every boot. (Note not using `enable` and no `[Install]` section in the `.service` file)


### NOTE ABOUT STP

**Activating STP** on a bridge caused the STFC network to disable the ethernet port, losing all connection. This means that STP should only be activated on a private network.

Without STP, it is important that no loops are created in the network. Ensure that the bluetooth bridge between the two PIs is only active when one of the PIs doesn't have ethernet connection. (Unless on an isolated network).

[Indepth notes on spanning tree (what happens in a loop?) and forwarding databases](http://linuxcommand.org/man_pages/brctl8.html)

### Turning bluez to debug mode

This is optional for debugging.

```bash
# Edit the same script as in serial setup
file=/lib/systemd/system/bluetooth.service
sudo sed -i.backup2 "/^ExecStart=/ s/$/ -d/" $file
sudo systemctl daemon-reload
sudo systemctl restart bluetooth
```

Logs are stored in `/var/log/syslog`

Fix an error like `org.bluez.Error.Rejected` then remeber to trust the connection in `bluetoothctl`
