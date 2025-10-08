# server/tools/homelab_status.py
import subprocess
import json
from mcp.types import TextContent
from server.registry import registry


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
    """Get AIMPH host status"""
    # Uptime
    uptime_result = ssh_command("aimph", "uptime -p")
    uptime = uptime_result["stdout"] if uptime_result["success"] else "unknown"
    
    # CPU usage
    cpu_result = ssh_command("aimph", "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
    cpu_usage = cpu_result["stdout"] if cpu_result["success"] else "unknown"
    
    # Memory
    mem_result = ssh_command("aimph", "free -h | awk 'NR==2{printf \"%s/%s (%.1f%%)\", $3,$2,($3/$2)*100}'")
    memory = mem_result["stdout"] if mem_result["success"] else "unknown"
    
    # Disk
    disk_result = ssh_command("aimph", "df -h / | awk 'NR==2{printf \"%s/%s (%s)\", $3,$2,$5}'")
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
    vm_list_result = ssh_command("aimph", "sudo virsh list --all")
    if not vm_list_result["success"]:
        return vms
    
    # Parse VM info
    vm_names = ["apps01", "db01", "gitlab01", "gitrunner01", "ops01"]
    
    for vm_name in vm_names:
        # Get VM info
        info_result = ssh_command("aimph", f"sudo virsh dominfo {vm_name}")
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
        
        # Get IP if available
        ip_map = {
            "apps01": "192.168.20.10",
            "db01": "192.168.30.10",
            "gitlab01": "192.168.40.10",
            "gitrunner01": "192.168.20.11",
            "ops01": "192.168.40.11"
        }
        
        vms.append({
            "name": vm_name,
            "state": state,
            "cpu": cpu,
            "memory": memory,
            "ip": ip_map.get(vm_name, "unknown")
        })
    
    return vms


def get_containers_status() -> list:
    """Get Docker containers on apps01"""
    containers = []
    
    result = ssh_command("aimph", "ssh apps01 'sudo docker ps --format \"{{.Names}}|{{.Status}}|{{.Ports}}\"'")
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
    
    # PostgreSQL on db01
    pg_result = ssh_command("aimph", "ssh db01 'ps aux | grep \"postgres -D\" | grep -v grep'")
    services["postgresql"] = {
        "vm": "db01",
        "status": "running" if pg_result["success"] and pg_result["stdout"] else "stopped"
    }
    
    # GitLab on gitlab01
    gitlab_result = ssh_command("aimph", "ssh gitlab01 'ps aux | grep gitlab | grep -v grep | head -1'")
    services["gitlab"] = {
        "vm": "gitlab01",
        "status": "running" if gitlab_result["success"] and gitlab_result["stdout"] else "stopped"
    }
    
    # GitLab Runner on gitrunner01
    runner_result = ssh_command("aimph", "ssh gitrunner01 'ps aux | grep gitlab-runner | grep -v grep | head -1'")
    services["gitlab_runner"] = {
        "vm": "gitrunner01",
        "status": "running" if runner_result["success"] and runner_result["stdout"] else "stopped"
    }
    
    # Grafana on ops01
    grafana_result = ssh_command("aimph", "ssh ops01 'ps aux | grep grafana.*server | grep -v grep'")
    services["grafana"] = {
        "vm": "ops01",
        "status": "running" if grafana_result["success"] and grafana_result["stdout"] else "stopped"
    }
    
    # Prometheus on ops01
    prom_result = ssh_command("aimph", "ssh ops01 'ps aux | grep prometheus | grep -v grep | head -1'")
    services["prometheus"] = {
        "vm": "ops01",
        "status": "running" if prom_result["success"] and prom_result["stdout"] else "stopped"
    }
    
    return services


def format_homelab_status(host: dict, vms: list, containers: list, services: dict) -> str:
    """Format comprehensive homelab status"""
    output = []
    
    # Header
    output.append("=" * 80)
    output.append("🏠 AIMPH HOMELAB STATUS")
    output.append("=" * 80)
    output.append("")
    
    # Host Status
    output.append("📊 HOST (AIMPH)")
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
        status_icon = "✅" if vm["state"] == "running" else "❌"
        output.append(f"  {status_icon} {vm['name']:<15} {vm['state']:<10} {vm['ip']:<16} {vm['cpu']} vCPU  {vm['memory']} RAM")
    output.append("")
    
    # Containers
    if containers:
        output.append("🐳 DOCKER CONTAINERS (apps01)")
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
    description="Get comprehensive status of AIMPH homelab: host resources, VMs, containers, and services",
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
