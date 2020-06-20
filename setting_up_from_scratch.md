# setting_up_from_scratch

## Initial setup
The latest Raspbian image can be downloaded from https://www.raspberrypi.org/downloads/raspbian/. 
The Lite image was used.

Burn the image to the an SD card. 

Add a file to the *boot* section called `ssh` (to enable the *ssh* connection). 

To prevent auto expansion of the file system to fill the SD card, edit `/boot/cmdline.txt` and delete this section of the line: `init=/usr/lib/raspi-config/init_resize.sh`

Put the card in the Pi and boot it. Ensure it is connected to the internet via an Ethernet cable.

By using the router page I checked for which new DHCP access had been granted to discover the IP address.

Log in using user name `pi` and password `raspberry`.

## Audio output
To make the audio come from the 3.5mm jack, run: `amixer cset numid=3 1`

## HDMI Always on
To force the HDMI to always be on, even if not plugged in at boot, uncomment the `hdmi_force_hotplug=1`
line in `/boot/config.txt` (using `sudo nano /boot/config.txt`)

## Extra Packages
Install the extra packages using:
```
sudo apt-get update
sudo apt-get install python-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsmpeg-dev python-numpy subversion libportmidi-dev ffmpeg libswscale-dev libavformat-dev libavcodec-dev
sudo apt-get install python3-pip
sudo apt-get install vsftpd hostapd dnsmasq
```

Setup vsFTPd (Very Secure FTP Deamon):
```
sudo nano /etc/vsftpd.conf
#Modify the file to set `#write_enable=YES` change to `write_enable=YES`
#Save using Ctrl-O, enter, and quit Ctrl-X
sudo service vsftpd restart
```

## WiFi Setup
On a RPi 3 (or above) setup the built in WiFi to act as an access point
```
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
```

Edit the local DHCP config
```bash
sudo nano /etc/dhcpcd.conf
#Then add to the end

# Add a static configuration for the wlan0
interface wlan0
static ip_address=192.168.250.1/24
denyinterfaces eth0
denyinterfaces wlan0
nohook wpa_supplicant
```

Setup the DHCP server (`dnsmasq`)

First copy the existing config file for reference and then open a new file
```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf

#Paste these lines
interface=wlan0
  dhcp-range=192.168.250.11,192.168.250.30,255.255.255.0,24h

#Allow as a DNS server
domain=local
expand-hosts
local=/local/
```

## Access point
Now configure the access point host software (`hostapd`)
```bash
sudo nano /etc/hostapd/hostapd.conf
```

Put in the following information, setup for SSID as `PyBongs` and password as `PyBongs1` (it needs to be 8 characters)
```bash
interface=wlan0
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
ssid=PiBells
wpa_passphrase=PiBells1
```

Configure the system to know where the config file we have just created is
```bash
sudo nano /etc/default/hostapd
```

Find the line `#DAEMON_CONF=` and replace it with `DAEMON_CONF="/etc/hostapd/hostapd.conf"`

Unmask hostapd:
```
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd
```

## Host name setup
Setup the `hosts` file with the name of the machine
```
sudo nano /etc/hosts
#Then add
#PyBongs WiFi network
192.168.250.1   pibells
```

## Python updates
Additional Python3 packages are required, install using:
```
sudo pip3 install pygame keyboard configparser pyserial
```

## Install the program
Open Filezilla (or other FTP program) and connect to the Pi, accessing as the user `pi` and the password `raspberry`.

Create the folder using `mkdir /home/pi/pibells` on the SSH connection.

Copy the files in.

Make the stop & shutdown scripts executable (not done by default when copying from Windows): `chmod +x /home/pi/pibells/stop_pibells.sh; chmod +x /home/pi/pibells/shutdown_script.sh`

## Displaying the welcome message
To display a welcome message before the user logs in, modify `/etc/issue`. This should contain the
contents of the `quick_reference` guide

To also make this display at SSH login, edit `/etc/ssh/sshd_config` and change the `Banner` line to the following
```
Banner /etc/issue
```

## Configuring to run at boot up
To make the application run at boot up, edit the `crontab` configuration. Run `crontab -e`. 
As this is the first use, it will ask which editor to use, `nano` should be the default so just press enter.

Add to the bottom of this file (which should just be full of comments lines beginning `#`) the following:
```
@reboot sudo nice -n -20 python3 /home/pi/pibells/pibells.py
```

## Streaming logs
To allow the log to be streamed to someone connected on the WiFi, nodejs needs to be setup:
```
curl -sL https://deb.nodesource.com/setup_9.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo apt-get install -y npm
sudo npm i frontail engine.io -g
```

To auto start: `@reboot sudo frontail -d /home/pi/pibells/pibells.log &` to `crontab -e`