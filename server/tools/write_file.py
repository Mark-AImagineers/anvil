import os

name = "write_file"
description = "Writes text content to a file, creating or overwriting as needed."

def run(params=None):
    if not params or "path" not in params or "content" not in params:
        return {"error": "Missing required parameters: 'path' and 'content'."}

    path = params["path"]
    content = params["content"]

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "path": os.path.abspath(path),
            "status": "written"
        }
    except Exception as e:
        return {"error": str(e)}
