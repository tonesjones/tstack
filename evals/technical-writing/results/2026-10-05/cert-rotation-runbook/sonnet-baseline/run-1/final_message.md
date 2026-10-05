I rewrote `RUNBOOK.md` in place as a checklist, a numbered procedure and a rollback section. I didn't run any of the commands.

- **Order fix:** The original added the `previous.pem` backup as an afterthought in the restart step. It's now its own step (step 3) before the swap.
- **Rollback:** It was a single clause. It now has explicit commands, restarts the service, re-checks health, and ends with `billingctl resume`.
- **Month-end warning:** The warning now sits in a "Before you start" list. I added that the alert gives 14 days, so you can wait out the close.
- **Cut:** I dropped the remark that the worker is the same as `billing-worker` in systemd. The title line now names the unit instead.

One thing I left alone but you should check. Step 1 says to save the `vault write` output to `new.pem`. By default that command prints a table, not a PEM file. You probably need `-format=json` plus extracting the certificate and key fields, but I don't know your setup. I kept the original wording rather than guess.

I added the escalation step in Rollback ("if it still fails, escalate in #billing-oncall"). That wasn't in the original.