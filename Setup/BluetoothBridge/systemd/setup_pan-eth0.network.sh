cat > /etc/systemd/network/pan-eth0.network << eof
[Match]
Name=eth0

[Network]
Bridge=br0
eof
