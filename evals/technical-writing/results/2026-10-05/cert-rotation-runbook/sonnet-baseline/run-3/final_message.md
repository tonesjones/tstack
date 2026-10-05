I rewrote `RUNBOOK.md` in place as a numbered procedure. I didn't run any of the commands or check them against the real environment.

- **Pre-checks first:** the month-end-close restriction, the VPN, and the `billing-ops` role now come before any step.
- **Backup step in order:** the old doc mentioned the `current.pem` → `previous.pem` copy as an afterthought. It is now step 3, before the swap.
- **Rollback section:** it restores `previous.pem` to `current.pem`, restarts, checks health, and resumes. The old doc only said to "restore previous.pem".
- **Removed:** the history about moving to Vault and the aside saying the worker is `billing-worker`. The service name is now stated once at the top.

I added three things that weren't in the original, so please check them:
- the roughly 10-minute duration estimate;
- the advice to wait for close to end if the alert fires then, since the alert fires 14 days before expiry;
- the "don't leave the rollback in place" note.

The doc also keeps the original's "save the output to `new.pem`" for the Vault step without saying how. Vault output normally includes the private key and chain. If there's a specific flag or extraction you use, add it there.