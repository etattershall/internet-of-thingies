# Alternate networking configuration

It appears that our current networking solution (dhcpcd.conf) isn't designed to setup bridge interfaces.
There are many resources that show how to setup persistant bridge interfaces using /etc/network/interfaces. However, this seems to be legacy and there is a message talking about conflicts between /etc/network/interfaces and dhcpcd.conf.

Instead, another option seems to be using `systemd` to configure the networking.

## Setting up the network to always function through the bridge

[There is a guide here](https://major.io/2015/03/26/creating-a-bridge-for-virtual-machines-using-systemd-networkd)

systemd can be used to setup the bridge from every boot so you always access the internet through `br0` rather than choosing between `eth0` or `bnep0` (bluetooth).

This only worked if I set the static ip address/ gateway using `systemd` rather than dhcpcd.conf. I couldn't get the DNS part of `systemd` to work so the standard method (dhcpcd.conf) is still used for that.

First remove `eth0` from dhcpcd.conf (we don't want eth0 to have an ip address) and set `br0` to:

```
interface br0
# static ip_address=130.246.77.144/22
# static routers=130.246.76.254
static domain_name_servers=130.246.8.13
```

Enable `systemd-networkd` and setup the network over systemd using `pan.network`, `br0.netdev` and `br0.network`.

```
sudo su
systemctl enable systemd-networkd

cat > /etc/systemd/network/pan.network << eof
[Match]
Name=eth0

[Network]
Bridge=br0
eof

cat > /etc/systemd/network/br0.netdev << eof
[NetDev]
Name=br0
Kind=bridge

eof

cat > /etc/systemd/network/br0.network << eof
[Match]
Name=br0

[Network]
Address=130.246.77.144/22
Gateway=130.246.76.254
eof
```
And reboot!

## Starting bluetooth pan server on boot
The bt-pan server can be run as a systemd service so that it is running from boot. To do this:
```
sudo cp pan.service.example.server /etc/systemd/system/
```
To check the status `sudo systemctl status pan`. To stop/start/restart: `sudo systemctl stop/start/restart pan`.
