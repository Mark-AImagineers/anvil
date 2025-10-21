# server/tools/email_search.py
from mcp.types import TextContent
from server.registry import registry
from server.utils.email_client import get_email_client
from imap_tools import AND, OR
from datetime import datetime, timedelta
import sys


@registry.register(
    name="email_search",
    description="Advanced search across emails with multiple criteria",
    input_schema={
        "type": "object",
        "properties": {
            "account": {
                "type": "string",
                "description": "Email account to search (markb or hello)",
                "enum": ["markb", "hello"],
                "default": "markb"
            },
            "folder": {
                "type": "string",
                "description": "Folder/mailbox to search in",
                "default": "INBOX"
            },
            "query": {
                "type": "string",
                "description": "Search query (searches in subject, from, and body)"
            },
            "from_address": {
                "type": "string",
                "description": "Filter by sender email address"
            },
            "subject": {
                "type": "string",
                "description": "Filter by subject keywords"
            },
            "body": {
                "type": "string",
                "description": "Search in email body"
            },
            "has_attachments": {
                "type": "boolean",
                "description": "Only show emails with attachments"
            },
            "unread_only": {
                "type": "boolean",
                "description": "Only show unread emails",
                "default": False
            },
            "since_days": {
                "type": "integer",
                "description": "Only show emails from last N days",
                "minimum": 1
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 50,
                "minimum": 1,
                "maximum": 200
            }
        },
        "required": []
    }
)
def email_search(arguments: dict) -> list[TextContent]:
    """Advanced email search"""
    
    account = arguments.get("account", "markb")
    folder = arguments.get("folder", "INBOX")
    query = arguments.get("query")
    from_address = arguments.get("from_address")
    subject = arguments.get("subject")
    body = arguments.get("body")
    has_attachments = arguments.get("has_attachments")
    unread_only = arguments.get("unread_only", False)
    since_days = arguments.get("since_days")
    limit = arguments.get("limit", 50)
    
    try:
        client = get_email_client(account)
        
        # Build search criteria
        criteria_list = []
        
        if query:
            # Search in multiple fields
            criteria_list.append(
                OR(
                    subject=query,
                    from_=query,
                    body=query
                )
            )
        
        if from_address:
            criteria_list.append(AND(from_=from_address))
        
        if subject:
            criteria_list.append(AND(subject=subject))
        
        if body:
            criteria_list.append(AND(body=body))
        
        if unread_only:
            criteria_list.append(AND(seen=False))
        
        if since_days:
            since_date = datetime.now().date() - timedelta(days=since_days)
            criteria_list.append(AND(date_gte=since_date))
        
        # Combine criteria
        if criteria_list:
            search_criteria = AND(*[c for c in criteria_list])
        else:
            search_criteria = AND(all=True)
        
        # Connect and search
        with client.get_imap_connection() as mailbox:
            mailbox.folder.set(folder)
            
            emails = []
            for msg in mailbox.fetch(search_criteria, reverse=True, limit=limit):
                # Apply attachment filter if needed (not directly supported in imap_tools)
                if has_attachments and len(msg.attachments) == 0:
                    continue
                
                email_info = {
                    "uid": msg.uid,
                    "subject": msg.subject or "(No Subject)",
                    "from": msg.from_ or "Unknown",
                    "date": msg.date.strftime("%Y-%m-%d %H:%M:%S") if msg.date else "Unknown",
                    "seen": msg.seen,
                    "size_kb": round(msg.size / 1024, 2) if msg.size else 0,
                    "attachments": len(msg.attachments),
                    "preview": msg.text[:100] + "..." if msg.text and len(msg.text) > 100 else msg.text or ""
                }
                emails.append(email_info)
            
            # Format output
            search_desc = []
            if query:
                search_desc.append(f"query='{query}'")
            if from_address:
                search_desc.append(f"from='{from_address}'")
            if subject:
                search_desc.append(f"subject='{subject}'")
            if body:
                search_desc.append(f"body='{body}'")
            if has_attachments:
                search_desc.append("with attachments")
            if unread_only:
                search_desc.append("unread only")
            if since_days:
                search_desc.append(f"last {since_days} days")
            
            result = f"🔍 Email Search Results for {client.email}\n"
            result += f"Folder: {folder}\n"
            result += f"Criteria: {', '.join(search_desc) if search_desc else 'all emails'}\n"
            result += f"Found: {len(emails)} email(s)\n"
            result += "=" * 80 + "\n\n"
            
            for i, email in enumerate(emails, 1):
                status = "📬 NEW" if not email["seen"] else "📭 Read"
                attach = f" 📎 {email['attachments']}" if email['attachments'] > 0 else ""
                
                result += f"{i}. {status}{attach}\n"
                result += f"   UID: {email['uid']}\n"
                result += f"   From: {email['from']}\n"
                result += f"   Subject: {email['subject']}\n"
                result += f"   Date: {email['date']}\n"
                result += f"   Preview: {email['preview']}\n"
                result += "-" * 80 + "\n"
            
            if len(emails) == 0:
                result += "No emails found matching the search criteria.\n"
            
            return [TextContent(type="text", text=result)]
            
    except Exception as e:
        error_msg = f"Error searching emails: {str(e)}"
        print(error_msg, file=sys.stderr)
        return [TextContent(type="text", text=error_msg)]
