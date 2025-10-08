import importlib
import pkgutil
import server.tools as tools_pkg

def load_tools():
    """Dynamically discover and import all tool modules."""
    tool_modules = []

    for _, module_name, _ in pkgutil.iter_modules(tools_pkg.__path__):
        full_name = f"{tools_pkg.__name__}.{module_name}"
        module = importlib.import_module(full_name)
        tool_modules.append(module)

    return tool_modules