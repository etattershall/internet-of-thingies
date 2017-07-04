# Alternate networking configuration

It appears that our current networking solution (`dhcpcd.conf`) isn't designed to setup bridge interfaces.
There are many resources that show how to setup persistant bridge interfaces using `/etc/network/interfaces`. However, this seems to be legacy and there is a message talking about conflicts between `/etc/network/interfaces` and `dhcpcd.conf`.

Instead, another option seems to be using systemd to configure the networking.

## Setting up the network to always function through the bridge

- [There is a guide here](https://major.io/2015/03/26/creating-a-bridge-for-virtual-machines-using-systemd-networkd)

- [Notes mainly from this site](https://www.linux.com/learn/understanding-and-using-systemd)
- [..And the blind blog](https://blind.guru/tag/bluetooth-pan.html)

systemd can be used to setup the bridge from every boot so you always access the internet through `br0` rather than choosing between `eth0` or `bnep0` (bluetooth).

This only worked if I set the static ip address/ gateway using systemd rather than `dhcpcd.conf`. I couldn't get the DNS part of systemd to work so the standard method (`dhcpcd.conf`) is still used for that.

First remove `eth0` from dhcpcd.conf (we don't want eth0 to have an ip address) and set `br0` to:

```
interface br0
# static ip_address=130.246.77.144/22
# static routers=130.246.76.254
static domain_name_servers=130.246.8.13
```

Enable `systemd-networkd` and setup the network over systemd using `pan.network`, `br0.netdev` and `br0.network`.

**Note that the static ip address needs to be changed in the br0.network file.**

```
sudo systemctl enable systemd-networkd

sudo cp pan-eth0.network /etc/systemd/network/
sudo cp pan-bnep0.network /etc/systemd/network/
sudo cp br0.netdev /etc/systemd/network/
sudo cp br0.network /etc/systemd/network/
```
And reboot!

## Starting bluetooth pan server/ client from systemd

### python-systemd

The python module `systemd` is required to run `bt-pan`. I couldn't get the python2 version to install (bt-pan is written in python2). Instead, I installed the python3 version using `sudo apt install python3-systemd` and converted `bt-pan` to python3 (see this directory).

### Server Side

The `bt-pan` server can be run as a systemd service so that it is running from boot. To do this:
```
sudo cp pan.service /etc/systemd/system/
sudo systemctl enable pan.service
```

- To check the status `sudo systemctl status pan`
- To stop/start/restart: `sudo systemctl stop/start/restart pan`


### Client Side
Setup as above but this service is simpler (although you can pass the bt address as an argument).
```
sudo cp pan@.service /etc/systemd/system/
# Start by specifying BT address...
systemctl start pan@B8:27:EB:96:85:A1
```
This will need to be run after every boot. (Note not using `enable` and no `[Install]` section in the `.service` file)
