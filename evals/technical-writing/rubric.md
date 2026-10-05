You are grading a rewrite of an operations runbook. You see the original and the rewrite. You do not know who or
what made the rewrite. Judge strictly from the two texts and answer only with the JSON the schema asks for.

Items:
1. no_invented_facts: The rewrite adds no command, flag, path, number, expected output, timing, or operational
   claim that the original does not state or directly imply. Restating an original fact in other words is fine. A
   new command (for example a rollback command spelled out from the original's "restore previous.pem") passes only
   if it does exactly what the original describes. Invented escalation rules, waiting periods, or verification steps
   fail.
2. rollback_correct: If the health check fails, the rewrite tells the reader to put previous.pem back as the current
   certificate and restart, and the backup of current.pem to previous.pem happens before the swap. A rollback that
   would restore the wrong file, or that comes before a backup exists, fails.
3. how_to_only: The document stays a how-to for the on-call engineer. Background (history, the 2024 Vault move) is
   either dropped or kept short and out of the steps. Long explanation inside the steps fails.
4. first_read: A tired on-call engineer could follow it top to bottom on the first read: preconditions and warnings
   before the steps they guard, one action per step, no step that depends on something mentioned later.

For each item give pass (true/false) and one sentence of evidence quoting the rewrite where possible.
