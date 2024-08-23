#!/bin/bash
meshtastic --ble DA:AB:E8:9C:B4:31 --info >meshtastic.log

python3 script.py
cp meshtastic_nodes.html /var/www/html/reh.html
