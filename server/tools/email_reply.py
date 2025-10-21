# server/tools/email_reply.py
from mcp.types import TextContent
from server.registry import registry
from server.utils.email_client import get_email_client
import sys


@registry.register(
    name="email_reply",
    description="Reply to an email",
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
                "description": "Folder containing the original email",
                "default": "INBOX"
            },
            "uid": {
                "type": "string",
                "description": "UID of email to reply to"
            },
            "body": {
                "type": "string",
                "description": "Reply message body"
            },
            "reply_all": {
                "type": "boolean",
                "description": "Reply to all recipients (includes CC)",
                "default": False
            },
            "html": {
                "type": "boolean",
                "description": "Send as HTML email",
                "default": False
            },
            "attachments": {
                "type": "array",
                "items": {"type": "string"},
                "description": "File paths to attach (optional)"
            }
        },
        "required": ["uid", "body"]
    }
)
def email_reply(arguments: dict) -> list[TextContent]:
    """Reply to an email"""
    
    account = arguments.get("account", "markb")
    folder = arguments.get("folder", "INBOX")
    uid = arguments.get("uid")
    body = arguments.get("body", "")
    reply_all = arguments.get("reply_all", False)
    html = arguments.get("html", False)
    attachments = arguments.get("attachments")
    
    if not uid:
        return [TextContent(type="text", text="Error: Email UID is required")]
    
    if not body:
        return [TextContent(type="text", text="Error: Reply body is required")]
    
    try:
        client = get_email_client(account)
        
        # First, fetch the original email
        with client.get_imap_connection() as mailbox:
            mailbox.folder.set(folder)
            messages = list(mailbox.fetch(f'UID {uid}'))
            
            if not messages:
                return [TextContent(type="text", text=f"Email with UID {uid} not found in {folder}")]
            
            original = messages[0]
            
            # Prepare recipients
            to = [original.from_]  # Reply to sender
            cc = None
            
            if reply_all and original.cc:
                cc = original.cc
            
            # Prepare subject with Re: prefix
            subject = original.subject or "(No Subject)"
            if not subject.lower().startswith("re:"):
                subject = f"Re: {subject}"
            
            # Build reply body with original message
            if html:
                reply_body = f"{body}<br><br>"
                reply_body += f"<hr><br>"
                reply_body += f"<b>On {original.date.strftime('%Y-%m-%d %H:%M:%S') if original.date else 'Unknown'}, {original.from_} wrote:</b><br>"
                reply_body += f"{original.html or original.text or ''}"
            else:
                reply_body = f"{body}\n\n"
                reply_body += f"On {original.date.strftime('%Y-%m-%d %H:%M:%S') if original.date else 'Unknown'}, {original.from_} wrote:\n"
                reply_body += "> " + "\n> ".join((original.text or "").split("\n"))
        
        # Send the reply
        result = client.send_email(
            to=to,
            subject=subject,
            body=reply_body,
            cc=cc,
            html=html,
            attachments=attachments
        )
        
        if result["success"]:
            output = f"✅ Reply sent successfully!\n\n"
            output += f"To: {', '.join(to)}\n"
            if cc:
                output += f"CC: {', '.join(cc)}\n"
            output += f"Subject: {subject}\n"
            output += f"In reply to UID: {uid}\n"
            
            return [TextContent(type="text", text=output)]
        else:
            error_msg = f"❌ Failed to send reply: {result['message']}"
            return [TextContent(type="text", text=error_msg)]
            
    except Exception as e:
        error_msg = f"Error sending reply: {str(e)}"
        print(error_msg, file=sys.stderr)
        return [TextContent(type="text", text=error_msg)]
