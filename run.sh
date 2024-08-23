#!/bin/bash
date
cd /home/yeraze/Development/pymeshdisplay
bluetoothctl disconnect DA:AB:E8:9C:B4:31
date
~/.local/bin/meshtastic --ble DA:AB:E8:9C:B4:31 --info >meshtastic.log
date

python3 script.py
cp meshtastic_nodes.html /var/www/html/reh.html
