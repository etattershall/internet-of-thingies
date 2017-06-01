#Installing pybluz on the Raspberry Pi **with** internet access

##Install bluez:
Instructions here: https://learn.adafruit.com/install-bluez-on-the-raspberry-pi/installation

##Install pybluez
pip install pybluz

##Install the debian adapter
sudo apt-get install python-bluez

##And finally...
sudo nano /etc/bluetooth/main.conf

Add to the bottom of the file:
DisablePlugins = pnat

Then restart your Raspberry Pi


#Installing pybluz on the Raspberry Pi **without** internet access

(tl;dr - it's really not pretty)


##Python-dev
sudo dpkg -i libpython2.7-dev_2.7.9-2+deb8u1_armhf.deb
sudo dpkg -i libpython-dev_2.7.9-1_armhf.deb
sudo dpkg -i python2.7-dev_2.7.9-2+deb8u1_armhf.deb
sudo dpkg -i python-dev_2.7.9-1_armhf.deb


##Bluez dependencies

Before we install bluex, we need to install six of its dependencies. Normally, it would 
be possible to get these (and all of *their* dependencies) using a package manager with 
the command:
sudo apt-get install -y libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev

Unfortunately, if we can't connect to the internet, we need to manually install a lot more packages 
(.deb files found at 
https://packages.debian.org/search?suite=default&section=all&arch=any&searchon=names&keywords=libusb)

**In this order**
sudo dpkg -i libusb-dev_0.1.12-25_armhf.deb
sudo dpkg -i libdbus-1-dev_1.8.22-0+deb8u1_armhf.deb
sudo dpkg -i libical1a_1.0-1.3_armhf.deb
sudo dpkg -i libical-dev_1.0-1.3_armhf.deb
sudo dpkg -i libudev-dev_215-17+deb8u6_armhf.deb
sudo dpkg -i libpcrecpp0_8.35-3.3+deb8u4_armhf.deb
sudo dpkg -i libpcre3-dev_8.35-3.3+deb8u4_armhf.deb
sudo dpkg -i libtinfo5_5.9+20140913-1+b1_armhf.deb
sudo dpkg -i libtinfo-dev_5.9+20140913-1+b1_armhf.deb
sudo dpkg -i libglib2.0-0_2.42.1-1+b1_armhf.deb
sudo dpkg -i libglib2.0-bin_2.42.1-1+b1_armhf.deb
sudo dpkg -i libglib2.0-dev_2.42.1-1+b1_armhf.deb
sudo dpkg -i libreadline6_6.3-8+b3_armhf.deb
sudo dpkg -i libreadline6-dev_6.3-8+b3_armhf.deb
sudo dpkg -i libreadline-dev_6.3-8+b3_armhf.deb

##Bluez
https://learn.adafruit.com/install-bluez-on-the-raspberry-pi/installation
tar xvf bluez-5.44.tar.xz
cd bluez-5.44/
./configure
make
sudo make install
sudo systemctl daemon-reload
systemctl status bluetooth

##pybluez-dependencies
sudo dpkg -i libbluetooth3_5.23-2+b1_armhf.deb
sudo dpkg -i libbluetooth-dev_5.23-2+b1_armhf.deb

And finally, thanks to:
https://www.raspberrypi.org/forums/viewtopic.php?f=32&t=45511
sudo dpkg -i python-bluez_0.22-1_armhf.deb

##Pybluez
sudo python setup.py install

Check by going into python shell (2.7) and running 
import bluetooth

##Finally

RFCOMM servers and clients will initially hang with the error 
BluetooothError(115, 'Operation now in process')

This is due to an issue with the bluez default settings in ubuntu/debian
(bediyap.com/linux/bluez-client-server-in-debian/)

It can be fixed by editing /etc/bluetooth/main.conf. Open the file using:
sudo nano /etc/bluetooth/main.conf

Add:
DisablePlugins = pnat

And restart bluetooth with:
sudo invoke-rc.d bluetooth restart

##Finally Finally...
Restart the Raspberry Pi! (else it will annoyingly hang with error 100: the network is down)

##Notes:

If, when you run the example script, you get error 111: connection refused, it means that you 
haven't manually paired with the arduino. You can pair by clicking on the bluetooth icon in 
the top right hand corner, scanning, selecting your device and inputting the four digit pin 
(default=1234)
