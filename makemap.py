from datetime import datetime
import folium
import html


def replace_unicode(s):
    # Decode the string to convert the Unicode escape sequences to actual characters
    decoded_string = (
        s.encode("utf-8")
        .decode("unicode_escape")
        .encode("utf-16", "surrogatepass")
        .decode("utf-16")
    )

    # Escape the Unicode characters to HTML entities
    escaped_html = "".join(
        f"&#{ord(char)};" if ord(char) > 127 else html.escape(char)
        for char in decoded_string
    )

    return escaped_html


# Function to convert timestamp to human-readable format
def convert_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


# Function to convert uptime seconds into a readable format
def format_uptime(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"


# Function to convert latitudeI/longitudeI to standard format
def convert_coordinates(coord):
    return coord / 1e7


# Function to parse the log file
def parse_log_file(log_file_path):
    nodes = []
    inside_node_section = False
    current_node = {}

    with open(log_file_path, "r", encoding="utf-8", errors="surrogatepass") as file:
        for rawline in file:
            line = rawline.strip()

            if line.startswith("Nodes in mesh:"):
                inside_node_section = True
                continue

            if inside_node_section:
                if line.endswith("{"):
                    continue

                if rawline.startswith("  },"):
                    if current_node:  # Only add if the current_node has been populated
                        nodes.append(current_node)
                    current_node = {}
                elif ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().strip('"')
                    value = replace_unicode(value.strip().strip(",").strip('"'))

                    if key in ["latitudeI", "longitudeI"]:
                        value = convert_coordinates(int(value))
                    elif key in ["num", "altitude", "snr", "uptime", "hopsAway"]:
                        value = float(value)
                    elif key == "lastHeard":
                        current_node["lastHeard_raw"] = int(value)
                        value = convert_time(int(value))

                    current_node[key] = value

    return nodes


# Function to generate HTML file
def generate_html(nodes, output_path):
    # Sort nodes by most recently seen
    nodes.sort(key=lambda x: x.get("lastHeard", ""), reverse=True)

    # Filter out nodes without valid latitude and longitude
    valid_nodes = [
        node for node in nodes if "latitudeI" in node and "longitudeI" in node
    ]

    # Determine the map center based on valid node coordinates
    if valid_nodes:
        map_center = (
            sum(node["latitudeI"] for node in valid_nodes) / len(valid_nodes),
            sum(node["longitudeI"] for node in valid_nodes) / len(valid_nodes),
        )
    else:
        map_center = (0, 0)

    m = folium.Map(location=map_center, zoom_start=12)

    m.add_css_link("randall_css", "reh.css")

    # Add markers to the map for each valid node
    for node in valid_nodes:
        if "latitudeI" not in node:
            continue
        age = 99999999
        color = "gray"
        if "lastHeard_raw" in node:
            age = datetime.now() - datetime.fromtimestamp(node["lastHeard_raw"])
            if age.days > 1:
                color = "gray"
            elif age.days < 0:
                color = "orange"
            else:
                color = "lightgreen"
        icon = "wifi"
        if "role" in node:
            if node["role"] == "ROUTER":
                icon = "signal"
            if node["role"] == "ROUTER_CLIENT":
                icon = "signal"

        popup_content = f"<span class='nobr'><b>{node.get('longName', 'Unknown')}-{node.get('shortName', 'Unknown')}</b></span><br>"
        popup_content += f"<span class='nobr'>Last Seen: {node.get('lastHeard', 'Unknown')}</span><br>"
        popup_content += (
            f"<span class='nobr'>MAC: {node.get('macaddr', 'Unknown')}</span><br>"
        )
        popup_content += (
            f"<span class='nobr'>Model: {node.get('hwModel', 'Unknown')}</span><br>"
        )
        popup_content += (
            f"<span class='nobr'>Uptime: {format_uptime(node.get('uptime', 0))}</span>"
        )

        folium.Marker(
            location=(node["latitudeI"], node["longitudeI"]),
            popup=popup_content,
            icon=folium.Icon(color=color, icon=icon),
            tooltip=f"[{node.get('shortName', 'Unknown')}] {node.get('longName', 'Unknown')}",
        ).add_to(m)

    # Save the map as HTML
    map_html = m._repr_html_()

    # Generate the HTML table with node details
    table_rows = ""
    for node in nodes:
        if "lastHeard" in node:
            age = datetime.now() - datetime.fromtimestamp(node["lastHeard_raw"])
            if age.days > 0:
                continue
            last_heard_formatted = node["lastHeard"]
            table_rows += f"""
            <tr>
                <td>{node.get('longName', 'Unknown')}</td>
                <td>{node.get('shortName', 'Unknown')}</td>
                <td>{node.get('snr', 'N/A')}</td>
                <td>{last_heard_formatted}</td>
                <td>{node.get('hopsAway', 'N/A')}</td>
            </tr>"""

    stamp = datetime.now().strftime("%c")
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Mesh Network Nodes</title>
        <style>
            table, th, td {{
                border: 1px solid black;
            }}
            th, td {{
                padding: 5px;
                text-align: left;
                font-size: -1;
            }}
            h3 {{
                font-size: 75%;
            }}
            .nobr {{
                white-space: nowrap !important;
            }}
            .overmap {{
                position: fixed;
                overflow: auto;
                top: 50px;
                left: 50px;
                width: 30em;
                height: 40em;
                z-index: 99;
            }}
            .tablebg {{
                background-color: #fefefe;
                margin: 2% auto; /* 15% from the top and centered */
                padding: 20px;
                border: 1px solid #888;
            }}
        </style>
    </head>
    <body>
        <h1>Mesh Network Nodes</h1>
        <div>{map_html}</div>
        <div class="overmap">
            <div class="tablebg">
            <h2>Node Details</h2>
            <h3>Last Updated {stamp}</h3>
            <table>
                <thead>
                    <tr>
                        <th>Long Name</th>
                        <th>Short Name</th>
                        <th>SNR</th>
                        <th>Last Seen</th>
                        <th>Hops</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            </div>
        </div>
    </body>
    </html>
    """

    # Write the HTML content to the output file
    with open(output_path, "w", encoding="utf-8", errors="surrogatepass") as file:
        file.write(html_content)


if __name__ == "__main__":
    # Specify the log file path and output HTML file path
    log_file_path = "meshtastic.log"
    output_path = "meshtastic_nodes.html"

    # Run the functions to parse the log and generate the HTML
    nodes = parse_log_file(log_file_path)
    generate_html(nodes, output_path)

    print("HTML file generated at:", output_path)
