# server/tools/homelab_vm.py
import subprocess
from mcp.types import TextContent
from server.registry import registry

try:
    from server.homelab_config import HOMELAB_HOST, get_vm_names
except ImportError:
    # Fallback if config doesn't exist
    HOMELAB_HOST = "homelab"
    def get_vm_names():
        return ["vm1", "vm2", "vm3", "vm4", "vm5"]


def ssh_command(host: str, command: str) -> dict:
    """Execute command via SSH and return result"""
    try:
        result = subprocess.run(
            ["ssh", host, command],
            capture_output=True,
            text=True,
            timeout=30
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


def get_vm_state(vm_name: str) -> str:
    """Get current state of a VM"""
    result = ssh_command(HOMELAB_HOST, f"sudo virsh domstate {vm_name}")
    if result["success"]:
        return result["stdout"].lower()
    return "unknown"


def start_vm(vm_name: str) -> dict:
    """Start a VM"""
    result = ssh_command(HOMELAB_HOST, f"sudo virsh start {vm_name}")
    return result


def stop_vm(vm_name: str, force: bool = False) -> dict:
    """Stop a VM (graceful shutdown or force)"""
    if force:
        result = ssh_command(HOMELAB_HOST, f"sudo virsh destroy {vm_name}")
    else:
        result = ssh_command(HOMELAB_HOST, f"sudo virsh shutdown {vm_name}")
    return result


def restart_vm(vm_name: str) -> dict:
    """Restart a VM"""
    result = ssh_command(HOMELAB_HOST, f"sudo virsh reboot {vm_name}")
    return result


def suspend_vm(vm_name: str) -> dict:
    """Suspend (pause) a VM"""
    result = ssh_command(HOMELAB_HOST, f"sudo virsh suspend {vm_name}")
    return result


def resume_vm(vm_name: str) -> dict:
    """Resume a suspended VM"""
    result = ssh_command(HOMELAB_HOST, f"sudo virsh resume {vm_name}")
    return result


@registry.register(
    name="homelab_vm",
    description="Manage VM lifecycle: start, stop, restart, suspend, resume VMs on homelab",
    input_schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["start", "stop", "restart", "suspend", "resume", "status", "list"],
                "description": "Action to perform on VM(s)"
            },
            "vm_name": {
                "type": "string",
                "description": "Name of VM (or 'all' for batch operations)"
            },
            "force": {
                "type": "boolean",
                "description": "Force stop (power off) instead of graceful shutdown",
                "default": False
            }
        },
        "required": ["action"]
    }
)
def homelab_vm(arguments: dict) -> list[TextContent]:
    """Manage VM lifecycle"""
    action = arguments.get("action")
    vm_name = arguments.get("vm_name")
    force = arguments.get("force", False)
    
    try:
        # Get available VMs from config
        available_vms = get_vm_names()
        
        # List all VMs
        if action == "list":
            output = ["Available VMs:"]
            for vm in available_vms:
                state = get_vm_state(vm)
                status_icon = "✅" if state == "running" else "❌" if state == "shut off" else "⏸️"
                output.append(f"  {status_icon} {vm:<15} - {state}")
            return [TextContent(type="text", text="\n".join(output))]
        
        # Require vm_name for other actions
        if not vm_name:
            return [TextContent(type="text", text="Error: vm_name is required for this action")]
        
        # Handle 'all' VMs
        if vm_name == "all":
            vms_to_process = available_vms
        else:
            if vm_name not in available_vms:
                return [TextContent(type="text", text=f"Error: Unknown VM '{vm_name}'. Available: {', '.join(available_vms)}")]
            vms_to_process = [vm_name]
        
        results = []
        
        for vm in vms_to_process:
            current_state = get_vm_state(vm)
            
            if action == "status":
                status_icon = "✅" if current_state == "running" else "❌" if current_state == "shut off" else "⏸️"
                results.append(f"{status_icon} {vm}: {current_state}")
            
            elif action == "start":
                if current_state == "running":
                    results.append(f"ℹ️  {vm} is already running")
                else:
                    result = start_vm(vm)
                    if result["success"]:
                        results.append(f"✅ {vm} started successfully")
                    else:
                        results.append(f"❌ Failed to start {vm}: {result['stderr']}")
            
            elif action == "stop":
                if current_state == "shut off":
                    results.append(f"ℹ️  {vm} is already stopped")
                else:
                    result = stop_vm(vm, force)
                    action_type = "force stopped" if force else "shutdown initiated"
                    if result["success"]:
                        results.append(f"✅ {vm} {action_type}")
                    else:
                        results.append(f"❌ Failed to stop {vm}: {result['stderr']}")
            
            elif action == "restart":
                if current_state != "running":
                    results.append(f"❌ Cannot restart {vm} - not currently running")
                else:
                    result = restart_vm(vm)
                    if result["success"]:
                        results.append(f"✅ {vm} restart initiated")
                    else:
                        results.append(f"❌ Failed to restart {vm}: {result['stderr']}")
            
            elif action == "suspend":
                if current_state != "running":
                    results.append(f"❌ Cannot suspend {vm} - not currently running")
                else:
                    result = suspend_vm(vm)
                    if result["success"]:
                        results.append(f"✅ {vm} suspended")
                    else:
                        results.append(f"❌ Failed to suspend {vm}: {result['stderr']}")
            
            elif action == "resume":
                if current_state != "paused":
                    results.append(f"❌ Cannot resume {vm} - not currently suspended")
                else:
                    result = resume_vm(vm)
                    if result["success"]:
                        results.append(f"✅ {vm} resumed")
                    else:
                        results.append(f"❌ Failed to resume {vm}: {result['stderr']}")
        
        return [TextContent(type="text", text="\n".join(results))]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error managing VMs: {str(e)}")]
