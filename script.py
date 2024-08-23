import json
from datetime import datetime
import folium

# Function to convert timestamp to human-readable format
def convert_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

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

    with open(log_file_path, 'r') as file:
        for line in file:
            line = line.strip()

            if line.startswith('Nodes in mesh:'):
                inside_node_section = True
                continue

            if inside_node_section:
                if line.endswith('{'):
                    continue

                if line.endswith('}'):
                    if current_node:  # Only add if the current_node has been populated
                        nodes.append(current_node)
                    current_node = {}
                elif ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().strip('"')
                    value = value.strip().strip(',').strip('"')

                    if key in ['latitudeI', 'longitudeI']:
                        value = convert_coordinates(int(value))
                    elif key in ['num', 'altitude', 'snr', 'uptime']:
                        value = float(value)
                    elif key == 'lastHeard':
                        value = convert_time(int(value))

                    current_node[key] = value

    return nodes

# Function to generate HTML file
def generate_html(nodes, output_path):
    # Sort nodes by most recently seen
    nodes.sort(key=lambda x: x.get('lastHeard', ''), reverse=True)

    # Filter out nodes without valid latitude and longitude
    valid_nodes = [node for node in nodes if 'latitudeI' in node and 'longitudeI' in node]

    # Determine the map center based on valid node coordinates
    if valid_nodes:
        map_center = (sum(node['latitudeI'] for node in valid_nodes) / len(valid_nodes),
                      sum(node['longitudeI'] for node in valid_nodes) / len(valid_nodes))
    else:
        map_center = (0, 0)

    m = folium.Map(location=map_center, zoom_start=12)

    # Add markers to the map for each valid node
    for node in valid_nodes:
        popup_content = f"Last Seen: {node.get('lastHeard', 'Unknown')}<br>"
        popup_content += f"MAC: {node.get('macaddr', 'Unknown')}<br>"
        popup_content += f"Model: {node.get('hwModel', 'Unknown')}<br>"
        popup_content += f"Uptime: {format_uptime(node.get('uptime', 0))}"

        folium.Marker(
            location=(node['latitudeI'], node['longitudeI']),
            popup=popup_content,
            tooltip=f"{node.get('longName', 'Unknown')}-{node.get('shortName', 'Unknown')}"
        ).add_to(m)

    # Save the map as HTML
    map_html = m._repr_html_()

    # Generate the HTML table with node details
    table_rows = ""
    for node in nodes:
        last_heard_formatted = node['lastHeard'] if 'lastHeard' in node else 'Unknown'
        table_rows += f"""
        <tr>
            <td>{node.get('longName', 'Unknown')}</td>
            <td>{node.get('shortName', 'Unknown')}</td>
            <td>{node.get('num', 'Unknown')}</td>
            <td>{node.get('snr', 'N/A')}</td>
            <td>{last_heard_formatted}</td>
        </tr>"""

    html_content = f"""
    <html>
    <head>
        <title>Mesh Network Nodes</title>
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            table, th, td {{
                border: 1px solid black;
            }}
            th, td {{
                padding: 10px;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <h1>Mesh Network Nodes</h1>
        <div>{map_html}</div>
        <h2>Node Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Long Name</th>
                    <th>Short Name</th>
                    <th>ID</th>
                    <th>SNR</th>
                    <th>Last Seen</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </body>
    </html>
    """

    # Write the HTML content to the output file
    with open(output_path, 'w') as file:
        file.write(html_content)

# Specify the log file path and output HTML file path
log_file_path = 'meshtastic.log'
output_path = 'meshtastic_nodes.html'

# Run the functions to parse the log and generate the HTML
nodes = parse_log_file(log_file_path)
generate_html(nodes, output_path)

print("HTML file generated at:", output_path)

