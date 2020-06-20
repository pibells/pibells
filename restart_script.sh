#!/bin/bash

#Script to Restart the application, after a brief timeout

sleep 3
sudo nice -n -20 python3 /home/pi/pibells/pibells.py &