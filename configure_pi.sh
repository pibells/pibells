#!/bin/bash

#Script to automate the installation of PiBells
# To run this before setting anything up, copy it and paste (right-click) into a putty window
# It will write the contents into a file and then run it

#Using heredoc: https://stackoverflow.com/a/25443034
cat > pibells_setup.sh << HERE
#!/bin/bash

#Set colours
#https://misc.flogisoft.com/bash/tip_colors_and_formatting
NO_COLOUR="\e[0m"
RED="\e[31m"
BLUE="\e[34m"
BOLD="\e[1m"
GREEN="\e[32m"
INSTALL_LOCATION="/home/pi/pibells"
LOG_FILE="pibells_setup.log"

#Exit if any error
set -e

## Audio output
printf "%b\n" "\${BOLD}\${BLUE}Setting mixer output to Audio jack \${NO_COLOUR}" | tee -a \${LOG_FILE}
amixer cset numid=3 1

## HDMI Always on
printf "%b\n" "\${BOLD}\${BLUE}Setting HDMI to always on\${NO_COLOUR}" | tee -a \${LOG_FILE}
sudo sed -i 's|#hdmi_force_hotplug=1|hdmi_force_hotplug=1|g' /boot/config.txt

## Extra Packages
printf "%b\n" "\${BOLD}\${BLUE}Installing extra packages\${NO_COLOUR}" | tee -a \${LOG_FILE}
sudo apt-get update --allow-releaseinfo-change >> \${LOG_FILE}
sudo apt-get update >> \${LOG_FILE}
sudo apt-get -y install python-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsmpeg-dev python-numpy subversion libportmidi-dev ffmpeg libswscale-dev libavformat-dev libavcodec-dev python3-pip vsftpd hostapd dnsmasq >> \${LOG_FILE}

## Python packages
printf "%b\n" "\${BOLD}\${BLUE}Installing python packages\${NO_COLOUR}" | tee -a \${LOG_FILE}
sudo pip3 install pygame keyboard configparser pyserial >> \${LOG_FILE}

## Setup VSFTPd
printf "%b\n" "\${BOLD}\${BLUE}Configuring VSFTPd\${NO_COLOUR}" | tee -a \${LOG_FILE}
sudo sed -i 's|#write_enable=YES|write_enable=YES|g' /etc/vsftpd.conf
sudo service vsftpd restart

## Streaming logs
printf "%b\n" "\${BOLD}\${BLUE}Configuring streaming logs\${NO_COLOUR}" | tee -a \${LOG_FILE}
curl -sL https://deb.nodesource.com/setup_9.x | sudo -E bash -
sudo apt-get install -y nodejs npm  >> \${LOG_FILE}
sudo npm i frontail engine.io -g >> \${LOG_FILE}

## WiFi Setup
printf "%b\n" "\${BOLD}\${BLUE}Setting up access point\${NO_COLOUR}" | tee -a \${LOG_FILE}
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

#Edit the local DHCP config
cat >> /etc/dhcpcd.conf <<EOF

# Add a static configuration for the wlan0
interface wlan0
static ip_address=192.168.250.1/24
denyinterfaces eth0
denyinterfaces wlan0
nohook wpa_supplicant
EOF

#Setup the DHCP server (`dnsmasq`)
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo su -c "cat > /etc/dnsmasq.conf <<EOF
interface=wlan0
  dhcp-range=192.168.250.11,192.168.250.30,255.255.255.0,24h

#Allow as a DNS server
domain=local
expand-hosts
local=/local/
EOF" root

## Access point
sudo su -c "cat >> /etc/hostapd/hostapd.conf <<EOF

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
EOF" root

#Configure the system to know where the config file we have just created is
sudo sed -i 's|#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|g' /etc/default/hostapd

#Unmask hostapd:
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd

## Host name setup
sudo su -c "cat >> /etc/hosts <<EOF

#PyBongs WiFi network
192.168.250.1   pibells
EOF" root

## Manually copy in the files
mkdir -p \${INSTALL_LOCATION}
printf "IP address: %s\n" "$(hostname -I | awk '{print $1}')"
printf "Copy the following files:\n"
printf "\tAll .py files\n"
printf "\tAll .wav files\n"
printf "\tquick_reference.txt\n"
read -p "Copy the files over FTP to \${INSTALL_LOCATION}, press [enter] when ready"

## Set the scripts to executable
cd \${INSTALL_LOCATION} && chmod +x *.sh

## Configure crontab
# See: https://stackoverflow.com/a/9625233 and https://stackoverflow.com/a/13355743
printf "%b\n" "\${BOLD}\${BLUE}Configuring crontab to start pybells & frontail\${NO_COLOUR}"  | tee -a \${LOG_FILE}
printf "Crontab before\n"
set +e; crontab -l; set -e

(crontab -l 2>/dev/null; echo "@reboot sudo nice -n -20 python3 \${INSTALL_LOCATION}/pibells.py";) | sort -u - | crontab -
(crontab -l 2>/dev/null; echo "@reboot sudo frontail -d \${INSTALL_LOCATION}/pibells.log") | sort -u - | crontab -
printf "Crontab after\n"
crontab -l

## Displaying the welcome message
printf "%b\n" "\${BOLD}\${BLUE}Configuring welcome message\${NO_COLOUR}"  | tee -a \${LOG_FILE}
sudo su -c "cat \${INSTALL_LOCATION}/quick_reference.txt > /etc/issue" root

# Setup the SSH banner
sudo sed -i 's|#Banner.*|Banner /etc/issue|g' /etc/ssh/sshd_config

printf "%b\n" "\${BOLD}\${GREEN}Complete\${NO_COLOUR}" | tee -a \${LOG_FILE}
printf "%b\n" "Please restart the Pi to test the configuration"  | tee -a \${LOG_FILE}
HERE

#Make the script runnable
chmod +x pibells_setup.sh

./pibells_setup.sh
