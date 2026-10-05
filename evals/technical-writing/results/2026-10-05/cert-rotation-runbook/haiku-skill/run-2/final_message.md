Done. I've rewritten RUNBOOK.md as a pure how-to following the technical-writing standards:

**Key changes:**
- **Removed narrative**: Cut the history about moving to Vault and the conversational opening.
- **Moved conditions up front**: "Do not rotate during month-end close" is now in Prerequisites, not buried in a step.
- **Fixed the backup step**: It now comes before the swap (fixing the "I forgot to mention" problem). An on-call engineer will back up automatically.
- **Made instructions commands**: Every step is a clear verb phrase, not passive voice or hedging ("Roll back the certificate" not "can be rolled back").
- **Added expected output**: Step 6 explicitly says "You should see `ok`" so the engineer knows success.
- **Separated rollback**: It's its own section, not a confusing parenthetical.
- **Cut filler**: Removed "So basically", "Note that", "it's important to note", "actually", and "Questions? Ping...". These belong in Slack, not a runbook.
- **Real command names**: `billing-worker` and `billingctl` appear consistently, not as synonyms.

An on-call engineer can now scan the Before section, follow the numbered steps in order, and know exactly what success looks like.