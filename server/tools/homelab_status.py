# server/tools/homelab_status.py
import subprocess
import json
from mcp.types import TextContent
from server.registry import registry

try:
    from server.homelab_config import HOMELAB_HOST, VMS, get_vm_names, get_vm_ip
except ImportError:
    # Fallback if config doesn't exist
    HOMELAB_HOST = "homelab"
    VMS = {}
    def get_vm_names():
        return ["vm1", "vm2", "vm3", "vm4", "vm5"]
    def get_vm_ip(vm_name):
        return "192.168.x.x"


def ssh_command(host: str, command: str) -> dict:
    """Execute command via SSH and return result"""
    try:
        result = subprocess.run(
            ["ssh", host, command],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out"}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}


def get_host_status() -> dict:
    """Get homelab host status"""
    # Uptime
    uptime_result = ssh_command(HOMELAB_HOST, "uptime -p")
    uptime = uptime_result["stdout"] if uptime_result["success"] else "unknown"
    
    # CPU usage
    cpu_result = ssh_command(HOMELAB_HOST, "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
    cpu_usage = cpu_result["stdout"] if cpu_result["success"] else "unknown"
    
    # Memory
    mem_result = ssh_command(HOMELAB_HOST, "free -h | awk 'NR==2{printf \"%s/%s (%.1f%%)\", $3,$2,($3/$2)*100}'")
    memory = mem_result["stdout"] if mem_result["success"] else "unknown"
    
    # Disk
    disk_result = ssh_command(HOMELAB_HOST, "df -h / | awk 'NR==2{printf \"%s/%s (%s)\", $3,$2,$5}'")
    disk = disk_result["stdout"] if disk_result["success"] else "unknown"
    
    return {
        "uptime": uptime,
        "cpu_usage": cpu_usage,
        "memory": memory,
        "disk": disk
    }


def get_vm_status() -> list:
    """Get status of all VMs"""
    vms = []
    
    # Get VM list
    vm_list_result = ssh_command(HOMELAB_HOST, "sudo virsh list --all")
    if not vm_list_result["success"]:
        return vms
    
    # Parse VM info
    vm_names = get_vm_names()
    
    for vm_name in vm_names:
        # Get VM info
        info_result = ssh_command(HOMELAB_HOST, f"sudo virsh dominfo {vm_name}")
        if not info_result["success"]:
            continue
        
        # Parse dominfo output
        info_lines = info_result["stdout"].split('\n')
        state = "unknown"
        cpu = "unknown"
        memory = "unknown"
        
        for line in info_lines:
            if line.startswith("State:"):
                state = line.split(":", 1)[1].strip()
            elif line.startswith("CPU(s):"):
                cpu = line.split(":", 1)[1].strip()
            elif line.startswith("Used memory:"):
                mem_kb = line.split(":", 1)[1].strip().split()[0]
                memory = f"{int(mem_kb) // 1024 // 1024}GB"
        
        # Get IP from config
        ip = get_vm_ip(vm_name)
        
        vms.append({
            "name": vm_name,
            "state": state,
            "cpu": cpu,
            "memory": memory,
            "ip": ip
        })
    
    return vms


def get_containers_status() -> list:
    """Get Docker containers on apps VM"""
    containers = []
    
    # Use first apps VM from config
    apps_vm = next((vm for vm in get_vm_names() if "apps" in vm.lower()), None)
    if not apps_vm:
        return containers
    
    result = ssh_command(HOMELAB_HOST, f"ssh {apps_vm} 'sudo docker ps --format \"{{{{.Names}}}}|{{{{.Status}}}}|{{{{.Ports}}}}\"'")
    if not result["success"]:
        return containers
    
    for line in result["stdout"].split('\n'):
        if not line.strip():
            continue
        parts = line.split('|')
        if len(parts) >= 2:
            containers.append({
                "name": parts[0],
                "status": parts[1],
                "ports": parts[2] if len(parts) > 2 else ""
            })
    
    return containers


def get_services_status() -> dict:
    """Get status of key services"""
    services = {}
    
    # Find VMs by purpose from config
    db_vm = next((vm for vm in get_vm_names() if "db" in vm.lower()), None)
    gitlab_vm = next((vm for vm in get_vm_names() if "gitlab" in vm.lower() and "runner" not in vm.lower()), None)
    runner_vm = next((vm for vm in get_vm_names() if "runner" in vm.lower()), None)
    ops_vm = next((vm for vm in get_vm_names() if "ops" in vm.lower()), None)
    
    # PostgreSQL
    if db_vm:
        pg_result = ssh_command(HOMELAB_HOST, f"ssh {db_vm} 'ps aux | grep \"postgres -D\" | grep -v grep'")
        services["postgresql"] = {
            "vm": db_vm,
            "status": "running" if pg_result["success"] and pg_result["stdout"] else "stopped"
        }
    
    # GitLab
    if gitlab_vm:
        gitlab_result = ssh_command(HOMELAB_HOST, f"ssh {gitlab_vm} 'ps aux | grep gitlab | grep -v grep | head -1'")
        services["gitlab"] = {
            "vm": gitlab_vm,
            "status": "running" if gitlab_result["success"] and gitlab_result["stdout"] else "stopped"
        }
    
    # GitLab Runner
    if runner_vm:
        runner_result = ssh_command(HOMELAB_HOST, f"ssh {runner_vm} 'ps aux | grep gitlab-runner | grep -v grep | head -1'")
        services["gitlab_runner"] = {
            "vm": runner_vm,
            "status": "running" if runner_result["success"] and runner_result["stdout"] else "stopped"
        }
    
    # Grafana and Prometheus
    if ops_vm:
        grafana_result = ssh_command(HOMELAB_HOST, f"ssh {ops_vm} 'ps aux | grep grafana.*server | grep -v grep'")
        services["grafana"] = {
            "vm": ops_vm,
            "status": "running" if grafana_result["success"] and grafana_result["stdout"] else "stopped"
        }
        
        prom_result = ssh_command(HOMELAB_HOST, f"ssh {ops_vm} 'ps aux | grep prometheus | grep -v grep | head -1'")
        services["prometheus"] = {
            "vm": ops_vm,
            "status": "running" if prom_result["success"] and prom_result["stdout"] else "stopped"
        }
    
    return services


def format_homelab_status(host: dict, vms: list, containers: list, services: dict) -> str:
    """Format comprehensive homelab status"""
    output = []
    
    # Header
    output.append("=" * 80)
    output.append("🏠 HOMELAB STATUS")
    output.append("=" * 80)
    output.append("")
    
    # Host Status
    output.append("📊 HOST")
    output.append("-" * 80)
    output.append(f"  Uptime:     {host['uptime']}")
    output.append(f"  CPU Usage:  {host['cpu_usage']}%")
    output.append(f"  Memory:     {host['memory']}")
    output.append(f"  Disk:       {host['disk']}")
    output.append("")
    
    # VM Status
    output.append("💻 VIRTUAL MACHINES")
    output.append("-" * 80)
    for vm in vms:
        status_icon = "✅" if vm["state"] == "running" else "❌" if vm["state"] == "shut off" else "⏸️"
        # Mask IP for security
        masked_ip = vm['ip'].rsplit('.', 1)[0] + ".xxx" if '.' in vm['ip'] else vm['ip']
        output.append(f"  {status_icon} {vm['name']:<15} {vm['state']:<10} {masked_ip:<16} {vm['cpu']} vCPU  {vm['memory']} RAM")
    output.append("")
    
    # Containers
    if containers:
        output.append("🐳 DOCKER CONTAINERS")
        output.append("-" * 80)
        for container in containers:
            status_icon = "✅" if "Up" in container["status"] else "❌"
            ports = container["ports"][:50] + "..." if len(container["ports"]) > 50 else container["ports"]
            output.append(f"  {status_icon} {container['name']:<20} {container['status']:<25} {ports}")
        output.append("")
    
    # Services
    output.append("⚙️  KEY SERVICES")
    output.append("-" * 80)
    for service_name, service_info in services.items():
        status_icon = "✅" if service_info["status"] == "running" else "❌"
        output.append(f"  {status_icon} {service_name:<20} {service_info['status']:<10} on {service_info['vm']}")
    output.append("")
    
    # Summary
    running_vms = sum(1 for vm in vms if vm["state"] == "running")
    running_containers = sum(1 for c in containers if "Up" in c["status"])
    running_services = sum(1 for s in services.values() if s["status"] == "running")
    
    output.append("📈 SUMMARY")
    output.append("-" * 80)
    output.append(f"  VMs:         {running_vms}/{len(vms)} running")
    output.append(f"  Containers:  {running_containers}/{len(containers)} running")
    output.append(f"  Services:    {running_services}/{len(services)} running")
    output.append("")
    output.append("=" * 80)
    
    return "\n".join(output)


@registry.register(
    name="homelab_status",
    description="Get comprehensive status of homelab: host resources, VMs, containers, and services",
    input_schema={
        "type": "object",
        "properties": {
            "detailed": {
                "type": "boolean",
                "description": "Show detailed information (default: False)",
                "default": False
            }
        }
    }
)
def homelab_status(arguments: dict) -> list[TextContent]:
    """Get comprehensive homelab status"""
    try:
        # Gather all status information
        host_status = get_host_status()
        vm_status = get_vm_status()
        containers_status = get_containers_status()
        services_status = get_services_status()
        
        # Format output
        status_report = format_homelab_status(
            host_status,
            vm_status,
            containers_status,
            services_status
        )
        
        return [TextContent(type="text", text=status_report)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting homelab status: {str(e)}")]
