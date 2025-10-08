import os

name = "read_file"
description = "Reads and returns the content of a specified text file."

def run(params=None):
    if not params or "path" not in params:
        return {"error": "Missing required parameter: 'path'"}

    path = params["path"]

    if not os.path.exists(path):
        return {"error": f"File not found: {path}"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "path": os.path.abspath(path),
            "content": content
        }
    except Exception as e:
        return {"error": str(e)}