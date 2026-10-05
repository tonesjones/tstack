Done. I rewrote the runbook as a how-to guide for on-call use following the technical-writing skill. The changes:

- **Stripped preamble:** Removed history and background—an on-call engineer needs steps, not context.
- **Clear structure:** Prerequisites up front (including the month-end timing warning), then numbered steps, then rollback.
- **Active voice:** "Issue", "Drain", "Rotate"—commands as imperatives, not descriptions of what gets done.
- **Conditions first:** Prerequisites section says when not to run this, and each step that needs one has its condition clear.
- **One thought per step:** Each numbered step is one action. Expected output is explicit ("The response must be `ok`").
- **Cut noise:** Removed "basically", "which is nice", "Note that it's important", and the systemd terminology note (unnecessary detail).
- **Consistent naming:** "billing worker" throughout (not "worker" or "the consumer").
- **Real commands in code font:** The exact vault, systemctl, and curl calls, copy-paste ready.

An engineer woken up at 2 AM can scan the Prerequisites, follow the numbered steps, and know what success looks like.