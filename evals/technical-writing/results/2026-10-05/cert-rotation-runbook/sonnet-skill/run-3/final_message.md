I rewrote `RUNBOOK.md` in place as a how-to for on-call. I haven't run any of the commands.

- **Step order fixed:** The old text told you to back up `current.pem` to `previous.pem` in a trailing aside ("I forgot to mention that"). The backup is now its own step before the swap.
- **Rollback section:** Rollback is now a separate section. It restores `previous.pem`, restarts, re-checks health, resumes the consumer, and points you to #billing-oncall.
- **Prerequisites and month-end:** These come before the steps. They now say you can wait out month-end close, because the alert gives 14 days of margin.
- **Cut:** The history ("we used to do this by hand") and the filler asides.
- **Kept:** Every command, path, role name, and the Slack channel.

- **Rollback wording is mine:** The original said to restore `previous.pem` but gave no commands. I wrote the `cp`, restart, and health-check steps myself.
- **Output saving unchecked:** Step 2 says to save the `vault write` output to `new.pem`, as the original did. Vault's raw output may include more than the PEM. If it does, that step needs the exact extraction command, and I can add it if you give it to me.