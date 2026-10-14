# EBD Agent: setup

A standalone Claude Code agent for two jobs: the morning brief and the EBD Daily. It has no link to your website code.

## Setup (once)
1. Install Claude Code if you haven't: https://claude.com/claude-code
2. Unzip this folder anywhere, e.g. `~/ebd-agent`.
3. Open a terminal in the folder: `cd ~/ebd-agent`
4. Start it: `claude`
5. (Recommended) Pick the Sonnet model for this agent. Don't use the biggest model for routine work.

## Daily use
- Morning: type `/brief`
- Evening: type `/daily` and paste your links under it, one per line:

```
/daily
https://inc42.com/...
https://www.business-standard.com/...
```

Results are saved in `output/`:
- `YYYY-MM-DD-brief.md`
- `YYYY-MM-DD-daily.md` (plain)
- `YYYY-MM-DD-daily-website.md` (in the website template)

## Your template
Open `templates/daily-template.md` and replace it with your real template (keep `{{placeholders}}`).

## Rules live in one file
`CLAUDE.md` holds every rule (formats, no commentary, cover every link, etc.). To change how the agent behaves, edit that file. Past dailies in `output/` are used to catch repeat stories.

## Tips to keep usage low
- Start a fresh `claude` session each day (the files in `output/` carry the history).
- Send only the links you want covered.

## Security
Never paste API keys into chat or screenshots. This agent doesn't need an API key: Claude Code uses your Claude login.
