# server/tools/email_read.py
from mcp.types import TextContent
from server.registry import registry
from server.utils.email_client import get_email_client
import sys
import html


@registry.register(
    name="email_read",
    description="Read full email content by UID",
    input_schema={
        "type": "object",
        "properties": {
            "account": {
                "type": "string",
                "description": "Email account to use (markb or hello)",
                "enum": ["markb", "hello"],
                "default": "markb"
            },
            "folder": {
                "type": "string",
                "description": "Folder/mailbox containing the email",
                "default": "INBOX"
            },
            "uid": {
                "type": "string",
                "description": "Email UID to read"
            },
            "include_html": {
                "type": "boolean",
                "description": "Include HTML body if available",
                "default": False
            }
        },
        "required": ["uid"]
    }
)
def email_read(arguments: dict) -> list[TextContent]:
    """Read full email content"""
    
    account = arguments.get("account", "markb")
    folder = arguments.get("folder", "INBOX")
    uid = arguments.get("uid")
    include_html = arguments.get("include_html", False)
    
    if not uid:
        return [TextContent(type="text", text="Error: Email UID is required")]
    
    try:
        client = get_email_client(account)
        
        with client.get_imap_connection() as mailbox:
            mailbox.folder.set(folder)
            
            # Fetch single email by UID
            messages = list(mailbox.fetch(f'UID {uid}'))
            
            if not messages:
                return [TextContent(type="text", text=f"Email with UID {uid} not found in {folder}")]
            
            msg = messages[0]
            
            # Build result
            result = f"📧 Email Details\n"
            result += "=" * 80 + "\n\n"
            result += f"UID: {msg.uid}\n"
            result += f"From: {msg.from_}\n"
            result += f"To: {msg.to}\n"
            
            if msg.cc:
                result += f"CC: {msg.cc}\n"
            
            result += f"Subject: {msg.subject or '(No Subject)'}\n"
            result += f"Date: {msg.date.strftime('%Y-%m-%d %H:%M:%S') if msg.date else 'Unknown'}\n"
            result += f"Status: {'Read' if msg.seen else 'Unread'}\n"
            
            # Attachments
            if msg.attachments:
                result += f"\n📎 Attachments ({len(msg.attachments)}):\n"
                for att in msg.attachments:
                    size_kb = round(att.size / 1024, 2) if att.size else 0
                    result += f"  - {att.filename} ({size_kb} KB, {att.content_type})\n"
            
            # Body
            result += "\n" + "=" * 80 + "\n"
            result += "MESSAGE BODY:\n"
            result += "=" * 80 + "\n\n"
            
            if msg.text:
                result += msg.text
            elif msg.html and include_html:
                result += "\n[HTML Content]:\n"
                result += msg.html
            elif msg.html:
                result += "(HTML email - use include_html:true to view HTML content)\n"
            else:
                result += "(No text content)\n"
            
            return [TextContent(type="text", text=result)]
            
    except Exception as e:
        error_msg = f"Error reading email: {str(e)}"
        print(error_msg, file=sys.stderr)
        return [TextContent(type="text", text=error_msg)]
