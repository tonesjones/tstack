I rewrote `RUNBOOK.md` in place as a single how-to. I didn't run any of the commands.

- **Order fix:** The old doc added "copy `current.pem` to `previous.pem` before the swap" as an afterthought in the restart step. It's now its own step 3, before the swap. Without it, the rollback has nothing to restore.
- **Rollback section:** It's a separate section. I wrote the rollback commands myself, because the original only said "restore `previous.pem`". They copy `previous.pem` over `current.pem`, restart the service, and re-check health. Please confirm that matches how you roll back.
- **Month-end warning:** It moved from the middle of the drain step to a "Before you start" section.
- **Cut:** The Vault history ("which is nice") is gone, along with the filler and the "same thing as billing-worker" aside. That fact is now one plain sentence near the top.
- **Added:** An opening line says when to use the runbook, and a "Get help" section points to #billing-oncall.

I kept the commands and paths exactly as they were.