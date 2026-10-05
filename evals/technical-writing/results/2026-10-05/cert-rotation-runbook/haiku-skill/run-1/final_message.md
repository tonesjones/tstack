Done. I've rewritten RUNBOOK.md as a clean how-to for on-call engineers. The changes:

- **Stripped background and fluff**: Removed "basically", "Some history", and the explanation of Vault's automation. A how-to assumes you know why you're here.
- **Made every instruction a command**: "Issue a new certificate" instead of "The new cert is issued by running". Direct, clear.
- **Put conditions first**: Prerequisites section up front tells you when *not* to run this.
- **Fixed the procedure order**: The backup now happens before the swap (the original had it backwards in a footnote).
- **One thought per sentence**: Split confusing lines like "restart and check..." into separate steps with clear expected output.
- **Real names consistently**: "billing worker" throughout, not "worker", "consumer", or mixed references. "current.pem" and "previous.pem" are always used the same way.
- **Added clear verification**: "You should see `ok`" tells you what success looks like.
- **Rollback section**: Separated from the main flow so it's there if needed but doesn't clutter the happy path.

An on-call engineer can now scan the prerequisites, follow the numbered steps, and know what to do if it breaks.