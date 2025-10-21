# server/tools/email_folders.py
from mcp.types import TextContent
from server.registry import registry
from server.utils.email_client import get_email_client
import sys


@registry.register(
    name="email_folders",
    description="List all email folders/mailboxes in the account",
    input_schema={
        "type": "object",
        "properties": {
            "account": {
                "type": "string",
                "description": "Email account to use (markb or hello)",
                "enum": ["markb", "hello"],
                "default": "markb"
            }
        },
        "required": []
    }
)
def email_folders(arguments: dict) -> list[TextContent]:
    """List all folders in email account"""
    
    account = arguments.get("account", "markb")
    
    try:
        client = get_email_client(account)
        
        with client.get_imap_connection() as mailbox:
            folders = mailbox.folder.list()
            
            result = f"📁 Email Folders for {client.email}\n"
            result += "=" * 80 + "\n\n"
            
            for folder in folders:
                result += f"• {folder.name}\n"
                if folder.flags:
                    result += f"  Flags: {', '.join(folder.flags)}\n"
            
            result += f"\nTotal: {len(folders)} folder(s)\n"
            
            return [TextContent(type="text", text=result)]
            
    except Exception as e:
        error_msg = f"Error listing folders: {str(e)}"
        print(error_msg, file=sys.stderr)
        return [TextContent(type="text", text=error_msg)]
