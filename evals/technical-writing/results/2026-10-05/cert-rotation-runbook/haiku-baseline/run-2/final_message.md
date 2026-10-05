Done. I've rewritten RUNBOOK.md to be actionable for an on-call engineer:

**Key improvements:**
- **Prerequisites** section upfront so you can verify readiness before starting
- **Numbered steps** in chronological order, not scattered
- **Fixed the backup step** — it now happens before the swap, not mentioned as an afterthought
- **Clear verification** — shows expected output from the health check
- **Dedicated rollback section** with exact commands, not buried in step 5
- **Removed conversational language** — no background history or tangential details
- **Code blocks** for all commands and outputs for easy scanning and copy-paste

An engineer can now follow this top-to-bottom without needing to reorder steps or hunt for missing instructions.