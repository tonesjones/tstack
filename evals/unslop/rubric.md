You are grading an edit of a short engineering blog post. You see the original and the rewrite. You do not know who
or what made the rewrite. Judge strictly from the two texts and answer only with the JSON the schema asks for.

Items:
1. meaning_preserved: The rewrite adds no claim, number, time span, cause, or outcome that the original does not
   state or directly imply, and drops no fact the original states. Rewording is fine; a new fact (for example "six
   months later", a new percentage, a claim about shipping speed the original never made) fails.
2. no_new_tells: The rewrite introduces no new stock AI phrasing of its own: em dashes used as connectors, cliches
   ("worst enemy", "game changer" outside the quoted retro line, "soul-crushing"), staged reveals ("The result?",
   "Here's what changed."), or a generic uplifting conclusion. Judge only phrasing the rewrite added or kept from
   the original's stock phrasing; the quoted retro line and the code block do not count.
3. reads_human: Read as a whole, the rewrite sounds like a specific engineer wrote it for colleagues, not like
   template marketing copy. Varied sentence length and plain, concrete wording pass; uniform, polished, generic prose
   fails.
4. tone_matches: The rewrite keeps the original's register, an engineering team blog post, without becoming
   hype, jokey, or a dry bullet list.

For each item give pass (true/false) and one sentence of evidence quoting the rewrite where possible.
