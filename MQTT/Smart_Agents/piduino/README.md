## Running piduino relay automatically

(Followed instructions from http://www.instructables.com/id/Raspberry-Pi-Launch-Python-script-on-startup/)

- Copy and paste the piduino directory into home/pi/
- Make the launcher excutable using 'sudo chmod 755 launcher.sh'
- Create a directory home/pi/logs
- Call 'sudo crontab -e'
- Append the line '@reboot sh /home/pi/bbt/launcher.sh >/home/pi/logs/cronlog 2>&1' to the bottom of the crontab file.

Now, when you reboot your raspberry pi, the serial relay program should start automatically
