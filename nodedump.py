import meshtastic
import meshtastic.ble_interface
import makemap
from pubsub import pub
import time


def onReceive(packet, interface):
    if "decoded" in packet:
        message_bytes = packet["decoded"]["payload"]
        message_string = message_bytes.decode("utf-8")
        fptr = open("messages.txt", "a")
        fptr.write(message_string)
        fptr.write("\n")
        fptr.close()


if __name__ == "__main__":
    print("Attempting to open interface")
    iface = None
    for i in range(0, 5):
        try:
            iface = meshtastic.ble_interface.BLEInterface("DA:AB:E8:9C:B4:31")
            break
        except:
            print("[%i] Failed to open interface, retrying.." % i)
            time.sleep(1)
            continue

    if iface is None:
        print("Failed to open interface, Aborting...")
        exit(-1)

    pub.subscribe(onReceive, "meshtastic.receive.text")

    print("Entering main loop")
    cycleCount = 0
    for i in range(0, 10):
        print("Waiting for response.. %i" % i)
        time.sleep(5)
        if cycleCount % 10 == 0:
            # Dump nodes and generate map
            reducedNodes = []
            if iface.nodes is not None:
                for node in iface.nodes.values():
                    sNode = {}
                    if "position" in node:
                        if "latitude" in node["position"]:
                            sNode["latitudeI"] = node["position"]["latitude"]
                            sNode["longitudeI"] = node["position"]["longitude"]
                    sNode["snr"] = node.get("snr", 0)
                    sNode["num"] = node["num"]
                    if "node" in node:
                        sNode["uptime"] = node["deviceMetrics"].get("uptimeSeconds", 0)
                    else:
                        sNode["update"] = 0
                    sNode["lastHeard_raw"] = node.get("lastHeard", 0)
                    sNode["lastHeard"] = makemap.convert_time(node.get("lastHeard", 0))
                    sNode["role"] = node["user"].get("role", "Unknown")
                    sNode["longName"] = node["user"]["longName"]
                    sNode["shortName"] = node["user"]["shortName"]
                    sNode["hwModel"] = node["user"]["hwModel"]
                    sNode["macaddr"] = node["user"].get("macaddr", "UNKNOWN")
                    reducedNodes.append(sNode)
                print("Generating map...")
                makemap.generate_html(reducedNodes, "map.html")
        cycleCount += 1

    iface.close()
