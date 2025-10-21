# Email Client Utility
# Manages IMAP and SMTP connections for email tools

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from imap_tools import MailBox, AND
from typing import Optional, List, Dict, Any
import sys

try:
    from server.email_config import EMAIL_ACCOUNTS, DEFAULT_ACCOUNT
except ImportError:
    print("ERROR: email_config.py not found. Please create it from email_config.example.py", file=sys.stderr)
    EMAIL_ACCOUNTS = {}
    DEFAULT_ACCOUNT = None


class EmailClient:
    """Manages email connections and operations"""
    
    def __init__(self, account_name: Optional[str] = None):
        """Initialize email client for specified account"""
        self.account_name = account_name or DEFAULT_ACCOUNT
        
        if self.account_name not in EMAIL_ACCOUNTS:
            raise ValueError(f"Account '{self.account_name}' not found in email_config.py")
        
        self.config = EMAIL_ACCOUNTS[self.account_name]
        self.email = self.config["email"]
        self.password = self.config["password"]
        self.imap_host = self.config["imap_host"]
        self.imap_port = self.config["imap_port"]
        self.smtp_host = self.config["smtp_host"]
        self.smtp_port = self.config["smtp_port"]
        self.use_ssl = self.config.get("use_ssl", True)
    
    def get_imap_connection(self):
        """Get IMAP connection using context manager"""
        return MailBox(self.imap_host, self.imap_port).login(
            self.email, 
            self.password
        )
    
    def send_email(
        self, 
        to: List[str], 
        subject: str, 
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send an email via SMTP"""
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = ', '.join(to)
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Attach body
            body_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, body_type))
            
            # Attach files if any
            if attachments:
                for filepath in attachments:
                    try:
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            filename = filepath.split('/')[-1]
                            part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                            msg.attach(part)
                    except Exception as e:
                        print(f"Warning: Could not attach file {filepath}: {e}", file=sys.stderr)
            
            # Prepare recipients list
            recipients = to.copy()
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                server.login(self.email, self.password)
                server.sendmail(self.email, recipients, msg.as_string())
            
            return {
                "success": True,
                "message": f"Email sent successfully to {', '.join(to)}",
                "from": self.email,
                "to": to,
                "subject": subject
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to send email: {str(e)}"
            }
    
    def get_account_info(self) -> Dict[str, str]:
        """Get account information"""
        return {
            "account_name": self.account_name,
            "email": self.email,
            "imap_host": self.imap_host,
            "smtp_host": self.smtp_host
        }


def get_email_client(account_name: Optional[str] = None) -> EmailClient:
    """Factory function to get email client instance"""
    return EmailClient(account_name)
