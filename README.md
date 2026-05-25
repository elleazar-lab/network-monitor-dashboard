# Network Monitor Dashboard

A web-based network discovery tool that scans your local network and displays all connected devices with IP addresses, MAC addresses, and manufacturer information.

## Features

- **Network Discovery** - Scans all IPs on your local network (1-254)
- **Device Detection** - Shows IP, MAC address, and manufacturer
- **Fast Scanning** - Multi-threaded ping sweeps (scans 254 IPs in ~30 seconds)
- **Web Dashboard** - Clean, responsive interface
- **One-Click Refresh** - Rescan network anytime

## Technologies

| Category | Technologies |
|----------|--------------|
| Backend | Python, Flask |
| Networking | ARP, ICMP (ping), Sockets |
| Frontend | HTML5, CSS3, JavaScript |
| Deployment | Local server / Render.com |

## How It Works

1. **Detects your network** - Automatically finds your IP, gateway, and subnet
2. **Pings all devices** - Multi-threaded ping sweep of 254 IP addresses
3. **Gets MAC addresses** - Reads from ARP cache
4. **Identifies manufacturers** - Matches MAC prefixes to OUI database
5. **Displays results** - Clean web dashboard with all devices

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/network-monitor-dashboard.git
cd network-monitor-dashboard

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py