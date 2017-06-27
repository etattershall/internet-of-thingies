# Alternate networking configuration

It appears that our current networking solution (dhcpcd.conf) isn't designed to setup bridge interfaces.
There are many resources that show how to setup persistant bridge interfaces using /etc/network/interfaces. However, this seems to be legacy and there is a message talking about conflicts between /etc/network/interfaces and dhcpcd.conf.

Instead, another option seems to be using `systemd` to configure the networking.

## Setting up the network to always function through the bridge

[There is a guide here](https://major.io/2015/03/26/creating-a-bridge-for-virtual-machines-using-systemd-networkd)


After removing the entry in dhcpcd.conf (if not then you won't know this will work):
```
sudo su
systemctl enable systemd-networkd

# These are required for dns lookups
sudo systemctl enable systemd-resolved
sudo ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf

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
DNS=130.246.8.13
Address=130.246.77.144/22
Gateway=130.246.76.254
eof
```
And reboot!
