import meshtastic
import meshtastic.ble_interface
from pubsub import pub
import time

iface = meshtastic.ble_interface.BLEInterface("DA:AB:E8:9C:B4:31")


def onReceive(packet, interface):
    if "decoded" in packet:
        message_bytes = packet["decoded"]["payload"]
        message_string = message_bytes.decode("utf-8")
        fptr = open("messages.txt", "a")
        fptr.write(message_string)
        fptr.write("\n")
        fptr.close()


pub.subscribe(onReceive, "meshtastic.receive.text")

for i in range(0, 10):
    print("Waiting for response.. %i" % i)
    time.sleep(1)

iface.close()
