# server/tools/email_list.py
from mcp.types import TextContent
from server.registry import registry
from server.utils.email_client import get_email_client
from imap_tools import AND
from datetime import datetime, timedelta
import sys


@registry.register(
    name="email_list",
    description="List emails from inbox or specified folder with optional filters",
    input_schema={
        "type": "object",
        "properties": {
            "account": {
                "type": "string",
                "description": "Email account to use (markb or hello). Defaults to markb",
                "enum": ["markb", "hello"],
                "default": "markb"
            },
            "folder": {
                "type": "string",
                "description": "Folder/mailbox to list from",
                "default": "INBOX"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of emails to return",
                "default": 20,
                "minimum": 1,
                "maximum": 100
            },
            "unread_only": {
                "type": "boolean",
                "description": "Only show unread emails",
                "default": False
            },
            "from_filter": {
                "type": "string",
                "description": "Filter by sender email/name (optional)"
            },
            "subject_filter": {
                "type": "string",
                "description": "Filter by subject keywords (optional)"
            },
            "since_days": {
                "type": "integer",
                "description": "Only show emails from last N days (optional)",
                "minimum": 1
            }
        },
        "required": []
    }
)
def email_list(arguments: dict) -> list[TextContent]:
    """List emails from mailbox with filters"""
    
    account = arguments.get("account", "markb")
    folder = arguments.get("folder", "INBOX")
    limit = arguments.get("limit", 20)
    unread_only = arguments.get("unread_only", False)
    from_filter = arguments.get("from_filter")
    subject_filter = arguments.get("subject_filter")
    since_days = arguments.get("since_days")
    
    try:
        client = get_email_client(account)
        
        # Build search criteria
        criteria_list = []
        
        if unread_only:
            criteria_list.append(AND(seen=False))
        
        if from_filter:
            criteria_list.append(AND(from_=from_filter))
        
        if subject_filter:
            criteria_list.append(AND(subject=subject_filter))
        
        if since_days:
            since_date = datetime.now().date() - timedelta(days=since_days)
            criteria_list.append(AND(date_gte=since_date))
        
        # Combine criteria
        if criteria_list:
            search_criteria = AND(*[c for c in criteria_list])
        else:
            search_criteria = AND(all=True)
        
        # Connect and fetch emails
        with client.get_imap_connection() as mailbox:
            mailbox.folder.set(folder)
            
            # Fetch emails
            emails = []
            for msg in mailbox.fetch(search_criteria, reverse=True, limit=limit):
                email_info = {
                    "uid": msg.uid,
                    "subject": msg.subject or "(No Subject)",
                    "from": msg.from_ or "Unknown",
                    "date": msg.date.strftime("%Y-%m-%d %H:%M:%S") if msg.date else "Unknown",
                    "seen": b'\\Seen' in msg.flags,
                    "size_kb": round(msg.size / 1024, 2) if msg.size else 0,
                    "has_attachments": len(msg.attachments) > 0
                }
                emails.append(email_info)
            
            # Format output
            result = f"📧 Email List for {client.email} ({folder})\n"
            result += f"Found {len(emails)} email(s)\n"
            result += "=" * 80 + "\n\n"
            
            for i, email in enumerate(emails, 1):
                status = "📬 NEW" if not email["seen"] else "📭 Read"
                attach = " 📎" if email["has_attachments"] else ""
                
                result += f"{i}. {status}{attach}\n"
                result += f"   UID: {email['uid']}\n"
                result += f"   From: {email['from']}\n"
                result += f"   Subject: {email['subject']}\n"
                result += f"   Date: {email['date']}\n"
                result += f"   Size: {email['size_kb']} KB\n"
                result += "-" * 80 + "\n"
            
            if len(emails) == 0:
                result += "No emails found matching the criteria.\n"
            
            return [TextContent(type="text", text=result)]
            
    except Exception as e:
        error_msg = f"Error listing emails: {str(e)}"
        print(error_msg, file=sys.stderr)
        return [TextContent(type="text", text=error_msg)]
