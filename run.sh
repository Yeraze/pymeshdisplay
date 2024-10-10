#!/bin/bash
date
cd /home/yeraze/Development/pymeshdisplay
bluetoothctl disconnect DA:AB:E8:9C:B4:31
date
~/.local/bin/meshtastic --ble DA:AB:E8:9C:B4:31 --info >meshtastic.log
date
if [ ! -s meshtastic.log ]; then
  date
  echo "Take 2"
  ~/.local/bin/meshtastic --ble DA:AB:E8:9C:B4:31 --info >meshtastic.log
  date
fi
if [ ! -s meshtastic.log ]; then
  date
  echo "Take 3"
  ~/.local/bin/meshtastic --ble DA:AB:E8:9C:B4:31 --info >meshtastic.log
  date
fi
if [ -s meshtastic.log ]; then
  python3 makemap.py
  cp meshtastic_nodes.html /var/www/html/reh.html
fi
