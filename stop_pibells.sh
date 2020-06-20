#!/bin/bash

#Script to stop a running PiBells instance

#Based on https://www.linuxquestions.org/questions/linux-general-1/how-to-kill-specific-python-script-389062/

sudo kill -9 $(ps aux | grep pibells.py | grep -v grep | awk '{ print $2 }')