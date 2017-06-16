
# Bridging LAN over bluetooth

## What is bridging

Joining two interfaces (eg `eth0` and `wlan0`) to the same network. This might be a way to join bluetooth to the rest of the internet. See [this page](https://wiki.debian.org/BridgeNetworkConnections) for more information.

### Installing
bridge-utils provides the tools to setup a bridge. For the moment, a python script `bt-pan` configures either end of the bluetooth setup. It is included in a library of misc tools.
```bash
sudo apt install bridge-utils
cd ~
git clone https://github.com/mk-fg/fgtk.git
```



### Setup

#### First time only

Edit `/etc/dhcpcd.conf` to add the standard settings for the bridge (should be exactly the same as `eth0` above it)

```
interface br0
static ip_address=130.246.77.144/22
static routers=130.246.76.254
static domain_name_servers=130.246.8.13
```

#### After every reboot

This script below creates the bridge interface `br0`. After running this, `ifconfig` should show that br0 has the ip address instead of `eth0`. All internet connectivity should remain the same but it will use the `br0` interface which contains the `eth0` as a slave.

TODO: Potentially need to set the broadcast address for `br0` but everything is working fine.

##### Host (connected to eth0)
```bash
sudo brctl addbr br0                                # Create the bridge
sudo brctl addif br0 eth0                           # Add eth0 to the bridge
sudo ip link set eth0 master br0                    # Set br0 eth0's master
sudo ip addr del 130.246.77.144/22 dev eth0         # Remove eth0's ip address
screen -dm /home/pi/fgtk/bt-pan --debug server br0  # Register bluetooth device with the bridge
```

Sources:
- [`brctl` cmds](https://wiki.debian.org/BridgeNetworkConnections)
- [`sudo ip link set eth0 master br0` ](https://superuser.com/questions/916368/does-a-bridge-between-2-tap-interfaces-need-an-ip-address)
- [Indepth notes on spanning tree (what happens in a loop?) and forwarding databases](http://linuxcommand.org/man_pages/brctl8.html)

##### Client (not connected to eth0)
```bash
screen -dm /home/pi/fgtk/bt-pan --debug client -w  B8:27:EB:96:85:A1
```


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
