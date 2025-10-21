# server/tools/email_send.py
from mcp.types import TextContent
from server.registry import registry
from server.utils.email_client import get_email_client
import sys


@registry.register(
    name="email_send",
    description="Send a new email",
    input_schema={
        "type": "object",
        "properties": {
            "account": {
                "type": "string",
                "description": "Email account to send from (markb or hello)",
                "enum": ["markb", "hello"],
                "default": "markb"
            },
            "to": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Recipient email addresses"
            },
            "subject": {
                "type": "string",
                "description": "Email subject"
            },
            "body": {
                "type": "string",
                "description": "Email body content"
            },
            "cc": {
                "type": "array",
                "items": {"type": "string"},
                "description": "CC recipients (optional)"
            },
            "bcc": {
                "type": "array",
                "items": {"type": "string"},
                "description": "BCC recipients (optional)"
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
        "required": ["to", "subject", "body"]
    }
)
def email_send(arguments: dict) -> list[TextContent]:
    """Send a new email"""
    
    account = arguments.get("account", "markb")
    to = arguments.get("to", [])
    subject = arguments.get("subject", "")
    body = arguments.get("body", "")
    cc = arguments.get("cc")
    bcc = arguments.get("bcc")
    html = arguments.get("html", False)
    attachments = arguments.get("attachments")
    
    # Validate inputs
    if not to:
        return [TextContent(type="text", text="Error: At least one recipient is required")]
    
    if not subject:
        return [TextContent(type="text", text="Error: Subject is required")]
    
    if not body:
        return [TextContent(type="text", text="Error: Body content is required")]
    
    try:
        client = get_email_client(account)
        
        result = client.send_email(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            html=html,
            attachments=attachments
        )
        
        if result["success"]:
            output = f"✅ Email sent successfully!\n\n"
            output += f"From: {result['from']}\n"
            output += f"To: {', '.join(result['to'])}\n"
            output += f"Subject: {result['subject']}\n"
            
            if cc:
                output += f"CC: {', '.join(cc)}\n"
            if bcc:
                output += f"BCC: {', '.join(bcc)}\n"
            if attachments:
                output += f"Attachments: {len(attachments)} file(s)\n"
            
            return [TextContent(type="text", text=output)]
        else:
            error_msg = f"❌ Failed to send email: {result['message']}"
            return [TextContent(type="text", text=error_msg)]
            
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(error_msg, file=sys.stderr)
        return [TextContent(type="text", text=error_msg)]
