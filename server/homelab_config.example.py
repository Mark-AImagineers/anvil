# server/homelab_config.example.py
"""
Example homelab configuration
Copy this to homelab_config.py and fill in your actual values
"""

# SSH Configuration
HOMELAB_HOST = "your-homelab-ssh-alias"  # SSH config alias

# VM Configuration
VMS = {
    "vm1": {
        "ip": "192.168.x.x",
        "vlan": "brXX",
        "purpose": "Application host",
        "services": ["Docker", "Services"]
    },
    "vm2": {
        "ip": "192.168.x.x",
        "vlan": "brXX",
        "purpose": "Database",
        "services": ["PostgreSQL"]
    },
    # Add more VMs as needed
}

# Get list of VM names
def get_vm_names():
    return list(VMS.keys())

# Get VM IP
def get_vm_ip(vm_name):
    return VMS.get(vm_name, {}).get("ip", "unknown")
