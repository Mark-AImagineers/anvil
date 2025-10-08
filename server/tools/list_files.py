import os

name = "list_files"
description = "List files and directories within a given path"

def run(params=None):
    path = params.get("path", ".") if params else "."
    try:
        items = os.listdir(path)
        return {
            "path": os.path.abspath(path),
            "items": items
        }
    except Exception as e:
        return {"error": str(e)}