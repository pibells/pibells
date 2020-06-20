PyBongs
=======

Installation
------------
PyBongs runs in Python 3.
Two modules are required, and need to be installed with pip

If python 3 is not the default python installation, then it may be necessary to install pip3 to install the modules
in python 3 (see: https://stackoverflow.com/a/13001357)
    sudo apt-get update
    #sudo apt install libsdl1.2-dev #needed with Stretch lite: https://raspberrypi.stackexchange.com/questions/66418/unable-to-run-sdl-config
    sudo apt-get install python-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsmpeg-dev python-numpy subversion libportmidi-dev ffmpeg libswscale-dev libavformat-dev libavcodec-dev
    sudo apt-get install python3-pip

    sudo apt-get install vsftpd

Configure vsftdp
    sudo nano /etc/vsftpd.conf
    #Modify the file to set `#write_enable=YES` change to `write_enable=YES`
    sudo service vsftpd restart

Install the module in /home/pi/pybongs
connect through FileZilla
Make the stop script executable
    chmod +x /home/pi/pybongs/stop_pibongs.sh
    chmod +x /home/pi/pybongs/shutdown_script.sh
    
Modules
-------
PyBongs requires the following modules:
    pygame ?
    keyboard
    configparser
Use
    sudo pip3 install pygame
    sudo pip3 install keyboard
    sudo pip3 install configparser

Setup
-----
To use the keyboard module, PyBongs must be run as root.
To make it run at start up, after starting the machine run:
    crontab -e
If an option for editor is presented, select nano - it may be the default
Scroll to the bottom (using the arrow keys) and enter the following line
    @reboot sudo nice -n -20 python3 /home/pi/pibells/pibells.py

Change the audio output to be 3.5mm jack (from: https://www.raspberrypi.org/documentation/configuration/audio-config.md)
    amixer cset numid=3 1
    

Usage
-----
PyBongs is designed to be run without a monitor and is controlled by a keyboard
A keyboard is not necessary if the additional options are not required.
The keyboard interface is described below:
    Pressing a single bell value 0-9, e, t will play the bell (if enabled)
    m + bell    will mute that bell number (always)
    u + bell    will unmute that bell number (but may not play if above the tenor)
    h + bell    will set that bell as the tenor
    f + bell    will make the bell sound 100th of a second earlier 
                (reduce the delay programmed into the photohead box)
    s + bell    will make the bell sound 100th of a second later 
                (increase the delay programmed into the photohead box)
    d + bell    will set the delay to the default delay (loaded from the config)
    r           will clear all the current settings (tenor and muting)
    l           will toggle debug logging on/off
    k + up/down will set the bells to be a ring of 12 in D (down) to a ring of 6 in D (up) through
                12 in D
                12 in E
                10 in F#
                9 in G
                8 in G#
                8 in A
                8 in A#
                7 in B
                6 in C
                6 in C#
                6 in D
    p           will toggle the playing of sounds when the bell numbers/letters are pressed
    q           shut down the application and power off the Pi
                this needs to be pressed twice 3 seconds
    z           restart the application (quicker than the Pi) - when the audio doesn't work correctly
                this needs to be pressed twice in 3 seconds

WiFi Access Point
-----------------
To make debugging easier (and potentially as a later point of control), the WiFi network of the RPi
has been setup to create an access point that can be connected to. 

Ideally this would be used to stream the log files (using existing open source projects) so that these
can be accessed during development.

Setting up the access point is described [here](https://thepi.io/how-to-use-your-raspberry-pi-as-a-wireless-access-point/)
```bash
sudo apt-get update
sudo apt-get install hostapd dnsmasq
```

Stop the installed services
```bash
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
```

This section doesn't appear to be needed any more
Setting up the network adaptor (from https://sirlagz.net/2012/08/09/how-to-use-the-raspberry-pi-as-a-wireless-access-pointrouter-part-1/)
sudo nano /etc/network/interfaces

Setup `wlan0` to be 
iface wlan0 inet static
address 192.168.250.1
netmask 255.255.255.0

**Note:** This is very important as many guides assumes the wired Ethernet is assigned an IP address and things are linking
through (I think). 

Edit the local DHCP config
```bash
sudo nano /etc/dhcpcd.conf
```

Then add to the end
```bash
# Add a static configuration for the wlan0
interface wlan0
static ip_address=192.168.250.1/24
denyinterfaces eth0
denyinterfaces wlan0
nohook wpa_supplicant
```

Not sure if the `nohook` is needed, from: https://pimylifeup.com/raspberry-pi-wireless-access-point/

Setup the DHCP server (`dnsmasq`)

First copy the existing config file for reference and then open a new file
```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```

Paste these lines
```bash
interface=wlan0
  dhcp-range=192.168.250.11,192.168.250.30,255.255.255.0,24h

#Allow as a DNS server
domain=local
expand-hosts
local=/local/
```

This will grant addresses in the range 192.168.250.11 to 30 for 24 hours

Setup the `hosts` file with the name of the machine
`sudo nano /etc/hosts`. Then add the following

```bash
#PyBongs WiFi network
192.168.250.1   pybongs
```



Now configure the access point host software (`hostapd`)
```bash
sudo nano /etc/hostapd/hostapd.conf
```

Put in the following information, setup for SSID as `PyBongs` and password as `PyBongs1` (it needs to be 8 characters).
There shouldn't be any trailing spaces in the config!
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
ssid=PyBongs
wpa_passphrase=PyBongs1
```

Configure the system to know where the config file we have just created is
```bash
sudo nano /etc/default/hostapd
```

Find the line `#DAEMON_CONF=` and replace it with `DAEMON_CONF="/etc/hostapd/hostapd.conf"`

Following the blog, there is no need to setup the port forwarding to the `eth0` interface. 
Nor any IP table rules.

### Debugging
This page (https://www.raspberrypi.org/forums/viewtopic.php?t=179618) contained the command 
`sudo hostapd -dd /etc/hostapd/hostapd.conf > /tmp/hostapd.log` to view what was happening when the 
WiFi network was not visible.


### Streaming Logs: https://github.com/mthenw/frontail
Installation help (for the nodejs) from here: https://github.com/mthenw/frontail/issues/105

```bash
curl -sL https://deb.nodesource.com/setup_9.x | sudo -E bash -
sudo apt-get install -y nodejs
```

npm i frontail -g ?? - didn't work from scratch as no npm (sudo apt-get install -y npm)
Setting up frontail to run at startup, add `@reboot frontail -d /home/pi/pybongs/PyBongs.log &` to `crontabe -e`

###
Issues with seeing network, but phone stuck at "authenticating" or "obtaining IP address"
This answer https://raspberrypi.stackexchange.com/a/25970 said the indication of the problem was
dnsmasq-dhcp[2699]: DHCP packet received on wlan0 which has no address
seen with tail -f /var/log/syslog

I did see that and setting up as per https://sirlagz.net/2012/08/09/how-to-use-the-raspberry-pi-as-a-wireless-access-pointrouter-part-1/
(now added above) solved the problem.

## Connecting
After connecting to the PyBongs network, navigate a browser to: `pybongs.local:9001` to get the log information

Copy Instructions
-----------------
cd ~/pybongs
sudo cp -R * /etc/ -v #don't do this!


Notes
-----
The settings are saved to an ini file and so will remain persistent between power cycles.

A stop script has been provided that will forcefully close PyBongs
It can be restarted with the commands
    cd /home/pi/pybongs
    sudo python3 pibongs.py

Raspbian Lite
-------------
When setting up from stratch, I used Raspbian Lite, which has a lot fewer packages built in, meaning they had to be installed manually.
This link (https://raspberrypi.stackexchange.com/questions/66418/unable-to-run-sdl-config) describes how to use apt-file to discover 
dependencies.

    sudo apt install apt-file
    sudo apt update

The missing dependencies were:
- sdl-config
- freetype2

The searching process didn't work quite as expected, but found the answer here: https://raspberrypi.stackexchange.com/a/92148

Hostapd Masked
--------------
When starting from scratch, I had this error when trying to start hostapd:
```
Failed to restart hostapd.service: Unit hostapd.service is masked.
```

The solution is to unmask and enable (https://github.com/raspberrypi/documentation/issues/1018)
```
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd
```

Auto FS expansion 
-----------------
From https://raspberrypi.stackexchange.com/questions/47773/disable-auto-file-system-expansion-in-new-jessie-image-2016-05-10
Open `/boot/cmdline.txt` and delete this line: `init=/usr/lib/raspi-config/init_resize.sh`

Resizing partition
------------------
From: https://raspberrypi.stackexchange.com/a/501

On a new Pi, after stopping the auto expansion:
- `sudo fdisk /dev/mmcblk0`
- `p` enter to view the partition tables
```bash
Disk /dev/mmcblk0: 14.9 GiB, 15931539456 bytes, 31116288 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0x0634f60c

Device         Boot  Start     End Sectors  Size Id Type
/dev/mmcblk0p1        8192  532480  524289  256M  c W95 FAT32 (LBA)
/dev/mmcblk0p2      540672 4292607 3751936  1.8G 83 Linux
```

- Note the Linux partition, with start position
- Now run
  - `d` enter (to delete)
  - `2` enter (for the second partition)
  - `n` enter (for a new partition)
  - `p` enter (for a primary partition)
  - `2` enter (for the partition number)
  - the start sector number from before (`540672`)
  - the new end sector number, to double the size, add the number of sector (`3751936`) to the end number (`4292607`)
  - `8044544` enter
  - `N` enter (to stop it deleting the ext4 signature
  - `w` enter to write
- `sudo reboot`
- after reboot
- `sudo resize2fs /dev/mmcblk0p2` to actually do the resize (may take some time)
- `sudo reboot`
- check the size with `df -h`

This worked well but when imaging with *Win32 Disk Imager*, it doesn't understand images, so takes a copy of all
of the SD card. 

However, we know that after 4292607 * 512 = 2,197,814,784 bytes, we don't card about the data.

This link https://github.com/Drewsif/PiShrink had a tool that was very close to what we wanted, but it
was trying to shrink the partition (which could be useful later).

Instead, I used Cygwin and `truncate` (used by the script above) to manually trim the image file to the desired size:
```bash
cd /cygdrive/c/test
truncate -s 2200000000 2019-06-20-raspbian-buster-lite-expanded-base.img
```

Buster becoming stable
----------------------

Got message:
```
pi@raspberrypi:~ $ sudo apt-get update
Get:1 http://archive.raspberrypi.org/debian buster InRelease [25.1 kB]
Get:2 http://raspbian.raspberrypi.org/raspbian buster InRelease [15.0 kB]
Get:3 http://archive.raspberrypi.org/debian buster/main armhf Packages [205 kB]
Reading package lists... Done
E: Repository 'http://raspbian.raspberrypi.org/raspbian buster InRelease' changed its 'Suite' value from 'testing' to 'stable'
N: This must be accepted explicitly before updates for this repository can be applied. See apt-secure(8) manpage for details.
```

From [this](https://superuser.com/a/1457007) link, need to run `apt-get update --allow-releaseinfo-change` to accept the change

Buffer underrun issues
----------------------
After getting the new Raspbian Lite (Buster) setup, the audio works when used slowly, but pressing buttons more often 
resulted in these error messages: `ALSA lib pcm.c:8424:(snd_pcm_recover) underrun occurred`

One suggestion was to increase the size of the pygame buffer. It was 64, to 512 but that didn't solve it completely, mostly
resulting in *some* bell sounds (from the keyboard) being missed (and those errors being generated). Increasing the latency further
just delayed the playing of the sounds, so this isn't the solution.

Searching more, I found this link: https://www.reddit.com/r/ChipCommunity/comments/53aly4/alsa_lib_pcmc7843snd_pcm_recover_underrun_occurred/
It suggested changing the pre-allocation buffer size `/proc/asound/card0/pcm0p/sub0/prealloc`. It was set to 128 (?) by default. 
This required becoming the super user
```
sudo su
echo 4096 > /proc/asound/card0/pcm0p/sub0/prealloc
```

This appeared to work well.

This is the configuration for the sound controller (?): https://alsa.opensrc.org/Proc_asound_documentation
- `/proc/asound` is the root of this configuration
- `card0/` is the first sound card
- `pcm0p/` is the playback stream (`p`) for the 0th `pcm` stream (pulse coded modulation)
- `sub0/` is the 0th substream information directory
- `prealloc` is the preallocation buffer size

Note: This is not a permenant setting, so will need to be applied every time 

Update (2019-07-20): By disabling the debug logging (now the default state), I haven't had any issues
Update (2019-07-21): Disabling the logging may have just been a fluke. 
Now I have added a 10ms wait after a reading the sounds seems more stable (with the limited testing I have done)

Setting the volume
------------------
https://raspberrypi.stackexchange.com/a/22087
amixer set PCM -- 1000

Initial message
---------------
The initial pre-login message is set in `/etc/issue`. This was setup to be the readme instructions

Recovering from bad clone
-------------------------
I was able to clone an RPi image, truncate it and flash it to another SD card. However, when starting, it generates some errors
and then boots with issues. I am unable to log in so clearly something is corrupted. 

When trying to flash the image back again, I had to reformat the SD card through Windows. The tool is "Disk Management".
Some notes are [here](https://www.easeus.com/partition-manager-software/format-sd-card-using-windows-cmd-and-formatter.html)

In Windows Explorer:
- right click on Computer
- Select "Manage"
- Click Storage -> Disk Management
- ?? Formatting the SD card to empty then writing the image again

SD Card Cloning Problems
------------------------
After setting up the SD card (with the small image size), I cloned it, truncated it, and then tried to write it again.

When starting up, I got the following error message on the HDMI output. It was repeated for several files
```bash
EXT4-fs error (device mmcblk0p2): ext4_lookup:1581: inode#11124 comm init: deleted inode referenced: 126187
```

I was unable to find much information about this but [here](https://askubuntu.com/a/841815) suggested it was due
to bad blocks on the target SD card (possible). These were where it was trying to write the image and so the inodes (file meta data)
were corrupted.

After this I was unable to log into the Pi through HDMI/directly as the user/password was not accepted. Watching it boot
there were plenty of errors so SSH then wouldn't work.

However, I was put the base image on this particular card. This also came up with errors but seemingly less bad:
```bash
EXT4-fs error (device mmcblk0p2): ext4_mb_generate_buddy:747: group 16, block bitmap and bg descriptor inconsistent: 25000 vs 26380 free clusters.
``` 

This might tally that there are bad clusters? However, I was still able to log in over SSH so must be good enough.