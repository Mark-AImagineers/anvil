# Security Policy

## Sensitive Information

**DO NOT** commit the following files or information:

### Protected Files
- `server/homelab_config.py` - Contains real IP addresses and hostnames
- `.ssh/` directory - SSH keys
- `.env` files - Environment variables
- Any files containing passwords, tokens, or API keys

### What IS Safe to Commit
- `server/homelab_config.example.py` - Example configuration template
- Tool code that references the config file
- Documentation with placeholder/example values

## Configuration Setup

1. **Initial Setup:**
   ```bash
   cp server/homelab_config.example.py server/homelab_config.py
   ```

2. **Fill in your actual values** in `server/homelab_config.py`

3. **Verify .gitignore:**
   ```bash
   git check-ignore server/homelab_config.py
   # Should output: server/homelab_config.py
   ```

## SSH Security

### Best Practices
- Use SSH key authentication (no passwords)
- Use `~/.ssh/config` for host aliases
- Set up passwordless sudo for specific commands only
- Never commit SSH private keys
- Use strong passphrases for SSH keys

### SSH Config Example
```
Host homelab
    HostName your-homelab-ip
    User your-username
    IdentityFile ~/.ssh/id_ed25519_homelab
    StrictHostKeyChecking no
```

## Network Security

- Private IP addresses (192.168.x.x, 10.x.x.x) are used throughout
- Tools operate within your local network only
- No external API exposure
- VLANs provide network segmentation

## Reporting Security Issues

If you find a security vulnerability in Anvil:
1. **DO NOT** open a public issue
2. Contact the maintainer directly
3. Provide detailed information about the vulnerability

## Security Checklist

Before committing:
- [ ] No real IP addresses in code
- [ ] No hostnames in code
- [ ] No passwords or tokens
- [ ] `homelab_config.py` is gitignored
- [ ] SSH keys are not included
- [ ] `.env` files are gitignored

## Code Review

All homelab tools:
- Reference `homelab_config.py` for sensitive data
- Use SSH aliases instead of direct IPs
- Include fallback values for missing config
- Validate input before executing commands

---

**Remember:** Anvil is designed for local, personal use. Never expose it to the public internet.
