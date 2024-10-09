import meshtastic
import meshtastic.ble_interface

iface = meshtastic.ble_interface.BLEInterface("DA:AB:E8:9C:B4:31")
if iface.nodes:
    __import__("pprint").pprint(iface.nodes)

iface.close()
