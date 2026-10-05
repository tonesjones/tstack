Done. I've rewritten the runbook with clear structure for on-call use:

- **Prerequisites and restrictions** upfront to prevent mistakes
- **Numbered steps** in proper logical order
- **Commands in code blocks** for easy copy-paste
- **Backup step** moved to the correct sequence (before cert swap)
- **Health verification** clearly marked
- **Troubleshooting section** for rollback procedures
- **Removed casual language** and background context

The runbook now guides an engineer through the full rotation without confusion or missing steps.