I rewrote `RUNBOOK.md` in place as a short pre-check list, six numbered steps and a separate rollback section. I didn't run any of the commands.

Changes beyond rewording:
- **Backup step:** the original added the "copy `current.pem` to `previous.pem`" step as an afterthought. I made it step 3, before the swap, since rollback depends on it.
- **Month-end warning:** the warning about not draining during month-end close moved into the checks at the top, before you start.
- **Rollback:** it now says to restore `previous.pem` into `current.pem`, restart, re-check health and resume the consumer. The original only said to "restore previous.pem".
- **Added line:** after a rollback, the old cert is still close to expiry, so I added a line telling the engineer to ask in #billing-oncall.
- **Cut:** the 2024 Vault history.

I kept the original instruction to save the `vault write` output to `new.pem` as written. It doesn't say how to do that, and Vault returns more than just the cert. Whoever owns the process should confirm that step.