# Email Configuration Example
# Copy this file to email_config.py and fill in your credentials

EMAIL_ACCOUNTS = {
    "markb": {
        "email": "your-email@domain.com",
        "password": "your-password-here",
        "imap_host": "mail.privateemail.com",
        "imap_port": 993,
        "smtp_host": "mail.privateemail.com",
        "smtp_port": 465,
        "use_ssl": True
    },
    "hello": {
        "email": "your-email@domain.com",
        "password": "your-password-here",
        "imap_host": "mail.privateemail.com",
        "imap_port": 993,
        "smtp_host": "mail.privateemail.com",
        "smtp_port": 465,
        "use_ssl": True
    }
}

# Default account to use if none specified
DEFAULT_ACCOUNT = "markb"
