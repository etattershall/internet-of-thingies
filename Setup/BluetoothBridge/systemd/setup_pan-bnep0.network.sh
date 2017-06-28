cat > /etc/systemd/network/pan-bnep0.network << eof
[Match]
Name=bnep0

[Network]
Bridge=br0
eof
