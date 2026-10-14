---
description: Build the EBD Daily from the article links I give you
argument-hint: <paste article links, one per line>
---

Build today's EBD Daily from these links:

$ARGUMENTS

Follow the "EBD Daily rules" in CLAUDE.md.

Steps:
1. List the links you received and confirm the count. If there are none in the message above, ask Veddika to paste them and stop.
2. Read `output/` for earlier dailies and note any story already covered.
3. For each link: open it and extract the facts. If it can't be opened, search for other coverage of the same story and write from that.
4. Write one card per link, in the order given. No skipped links.
5. Add the On the Radar block and the sign-off.
6. Save the plain version to `output/YYYY-MM-DD-daily.md`.
7. Then fill `templates/daily-template.md` (Title, Excerpt of the whole page, then each item as a bold headline line, the summary on the next line, and an italic Source line below it) and save it to `output/YYYY-MM-DD-daily-website.md`.
8. Print the website version in full. After it, outside the daily, list: repeats flagged, links that were blocked and how you covered them, and anything you couldn't verify.
