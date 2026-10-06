---
{{front_matter}}
---
# {{title}}

> {{meta_line}}

## Why this matters
<!-- WRITER: 2-4 sentences. Why this matters to a senior backend/AI engineer and why it sits here on the ladder. No filler. Delete every HTML comment before the lesson is sent. -->
{{#core}}
<!-- CURRICULUM SUMMARY for this rung ({{rung_id}}): {{summary}} -->
{{/core}}
{{#fresh}}
<!-- FRESH LESSON: built from today's research. Say what the item is, who published it, and why it is worth the reader's 20 minutes today. Fresh lessons need at least TWO verbatim quoted passages (blockquote + citation). -->
{{/fresh}}

{{#primer}}
## Primer
<!-- WRITER: this item sits above the reader's current level ({{reader_level_name}}) or its prerequisites are not done yet. 150-300 words: only the prerequisite ideas needed to follow the lesson, with inline citations. Delete this comment. -->

{{/primer}}
## The idea
<!-- WRITER: SELF-CONTAINED: explain everything in full; never point at existing repo notes instead of explaining (they may only be listed at the end of Sources under 'Related in your knowledge base'). BOOK TRACKS (ddia, fp-scala): restate the rung's chapter sections in the book's order — first line '> Chapter map: <book> ch. N — §N.1 <name>, §N.2 <name>', then one ### per section with its § number, the book's own running example, terms, argument and conclusion in your words; label anything extra 'Beyond the book:'. {{presentation_hint}} Exactly one or two mermaid code blocks (a fenced block whose info string is "mermaid"); no other diagram format. Subheadings (###) are allowed. 600-1200 words.
EVIDENCE RULE (SPEC section 4):
 - Claims from a book/course/page the reader can open: cite inline, with chapter / section / timestamp, e.g. (Kleppmann, DDIA ch. 3, "Hash Indexes"), (RFC 9000 section 7.2), (3Blue1Brown, "But what is a neural network?", 4:10).
 - Claims from a blog post, paper, release note, talk or news: a VERBATIM quote of 1-3 sentences in a blockquote, citation directly under it: > "..." - Author or organisation, Title, date, URL. Fetch the page and copy the quote; never paraphrase a quote as if it were verbatim and never invent one.
 - Numbers, benchmarks and dates carry their citation in the same sentence.
 - Every URL used appears in Sources; links are fetched and verified before sending. -->
{{#core}}
<!-- MUST COVER (key points):
{{key_points_list}}
DIAGRAM to draw in mermaid: {{diagram}} -->
{{/core}}

## Worked example
<!-- WRITER: 5-10 minutes, concrete and copy-pasteable. You may rename this heading to "## Lab" when the reader runs something. Follow the LAB RULE (SPEC section 4): one sentence stating the question the lab answers; ### Step 1/2/... headings; code that prints intermediate values (per row / per step), not only totals; RUN it and paste the real output; then a '### Reading the output' section: what each column/number means and which direction is better, the output as a table, the arithmetic traced with digits for at least one case, and a bold **Verdict** after each output block; finish with a numbered cause -> mechanism -> consequence -> what it means in practice chain. Delete this comment. -->
{{#core}}
<!-- EXAMPLE / LAB from the curriculum: {{example}} -->
{{/core}}

## Self-check
<!-- WRITER: exactly three questions, each with its answer hidden in details. Delete this comment. -->
1. <!-- question 1 --> <details><summary>Answer</summary><!-- answer 1 --></details>
2. <!-- question 2 --> <details><summary>Answer</summary><!-- answer 2 --></details>
3. <!-- question 3 --> <details><summary>Answer</summary><!-- answer 3 --></details>

## Sources
<!-- WRITER: one line per source: Author/Org, date, what it contributed, "accessed {{today}}". Every URL cited above must be listed; verify each link by fetching it. Core lessons from web sources need at least one verbatim quoted passage in The idea (blockquote + citation line with URL); fresh lessons at least two. -->
{{sources_block}}

## Next on this track
{{next_line}}
