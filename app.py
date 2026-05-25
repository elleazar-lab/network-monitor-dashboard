# app.py - Network Monitor Web Dashboard (Windows-compatible, no emojis)
from flask import Flask, render_template, jsonify
import socket
import subprocess
import threading
import re
from datetime import datetime

app = Flask(__name__)

# Cache for scan results
scan_results = {
    'devices': [],
    'last_scan': None,
    'network_info': {}
}

def get_network_info():
    """Get local network information"""
    info = {}
    
    # Get hostname and local IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    info['hostname'] = hostname
    info['local_ip'] = local_ip
    
    # Get public IP (using external service)
    try:
        import urllib.request
        public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
        info['public_ip'] = public_ip
    except:
        info['public_ip'] = 'Unable to fetch'
    
    # Calculate network range from local IP
    ip_parts = local_ip.split('.')
    info['network_base'] = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
    info['subnet'] = '255.255.255.0'
    info['gateway'] = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"
    
    return info

def ping_host(ip):
    """Ping a host to check if it's alive"""
    try:
        import platform
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        response = subprocess.run(
            ['ping', param, '1', ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        return response.returncode == 0
    except:
        return False

def get_mac_from_arp(ip):
    """Get MAC address from ARP cache"""
    try:
        import platform
        if platform.system().lower() == 'windows':
            result = subprocess.run(['arp', '-a', ip], capture_output=True, text=True, timeout=3)
            # Parse Windows ARP output
            for line in result.stdout.split('\n'):
                if ip in line:
                    mac_match = re.search(r'([0-9A-Fa-f]{2}[-:]){5}([0-9A-Fa-f]{2})', line)
                    if mac_match:
                        return mac_match.group(0).replace('-', ':')
        else:
            # Linux/Mac
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=3)
            for line in result.stdout.split('\n'):
                if ip in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        mac = parts[2]
                        if re.match(r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', mac):
                            return mac
    except:
        pass
    return 'Unknown'

def get_manufacturer(mac):
    """Identify manufacturer from MAC address (OUI lookup)"""
    if mac == 'Unknown' or not mac:
        return 'Unknown'
    
    # Common OUI database (first 6 characters of MAC)
    oui = mac.replace(':', '').upper()[:6]
    
    # Sample OUI database
    oui_db = {
        '000000': 'Xerox', '0001E6': 'Apple', '0003E9': 'Intel', '000A95': 'Samsung',
        '0016CB': 'Apple', '0021CC': 'Apple', '0050F2': 'Microsoft', '0090C9': 'Belkin',
        '00A0C9': 'Intel', '08002B': 'DEC', '0C2AE8': 'Raspberry Pi', '10FEED': 'Ubiquiti',
        '14DD99': 'Sony', '1C5A6B': 'Amazon', '24F5AA': 'Google', '2C303A': 'Nest',
        '30A9DE': 'HP', '34F39A': 'TP-Link', '3C286D': 'Ubiquiti', '40B87C': 'TCL',
        '44D9E7': 'Google', '4C3275': 'D-Link', '50C7BF': 'Arris', '54E075': 'Realtek',
        '5C93A2': 'Huawei', '60AB67': 'Belkin', '64BC58': 'OnePlus', '6C72E7': 'Philips',
        '70B3D5': 'Acer', '789ABB': 'ASUS', '7C05EF': 'LG', '7C531A': 'MikroTik',
        '80A589': 'Intel', '840B2E': 'TP-Link', '888686': 'Intel', '8C45DA': 'Zyxel',
        '8CB64B': 'AsusTek', '901D27': 'Intel', '94DE80': 'Espressif', '98927C': 'Amazon',
        '9C8E99': 'Xiaomi', 'A8D0E5': 'Acer', 'AC5F3E': 'Cisco', 'B09575': 'Vizio',
        'B45A42': 'Roku', 'B847C6': 'Atheros', 'BCAEC5': 'Raspberry Pi', 'C025E9': 'TP-Link',
        'C45BBE': 'Foxconn', 'CC2D21': 'Samsung', 'CC3322': 'Netgear', 'D05764': 'Intel',
        'D41A3F': 'LG', 'D85D4C': 'Google', 'DC44B2': 'Intel', 'E03593': 'ASRock',
        'E458E8': 'Nokia', 'E8ABFA': 'MikroTik', 'EC2274': 'Hitron', 'F03D64': 'Hitachi',
        'F06E9F': 'Netgear', 'F452EA': 'Xfinity', 'F80F41': 'Intel', 'FC1C2D': 'Dell',
        'FCA552': 'Technicolor',
    }
    
    return oui_db.get(oui, 'Unknown')

def scan_network():
    """Scan the local network for devices"""
    network_info = get_network_info()
    network_base = network_info['network_base']
    
    devices = []
    active_ips = []
    
    print(f"Scanning network {network_base}.0/24...")
    
    # First, ping all hosts to find active ones
    threads = []
    
    def check_ip(ip):
        if ping_host(ip):
            active_ips.append(ip)
    
    # Scan IPs 1-254 (skip .0 and .255)
    for i in range(1, 255):
        ip = f"{network_base}.{i}"
        thread = threading.Thread(target=check_ip, args=(ip,))
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print(f"Found {len(active_ips)} active devices")
    
    # Get details for each active IP
    for ip in active_ips:
        mac = get_mac_from_arp(ip)
        manufacturer = get_manufacturer(mac)
        
        devices.append({
            'ip': ip,
            'mac': mac,
            'manufacturer': manufacturer,
            'status': 'Up'
        })
    
    # Sort by IP
    devices.sort(key=lambda x: [int(i) for i in x['ip'].split('.')])
    
    return devices, network_info

@app.route('/')
def index():
    """Serve the dashboard"""
    return render_template('index.html')

@app.route('/api/scan')
def api_scan():
    """API endpoint to trigger a network scan"""
    global scan_results
    devices, network_info = scan_network()
    scan_results = {
        'devices': devices,
        'last_scan': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'network_info': network_info
    }
    return jsonify(scan_results)

@app.route('/api/status')
def api_status():
    """Get cached scan results"""
    return jsonify(scan_results)

if __name__ == '__main__':
    print("=" * 40)
    print("Network Monitor Dashboard")
    print("=" * 40)
    print("Starting web server...")
    print("Open http://127.0.0.1:5000 in your browser")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    app.run(debug=True, host='0.0.0.0', port=5000)
