# Proposal: changes to carry over to the rpg_kids canon repo

The export script was built against canon exactly as it is today and needed no
canon changes. Everything below is workflow, not file format.

## 1. Add a final step to the wrap-session skill

In `.claude/skills/wrap-session/SKILL.md`, after step 3 (commit and push) and the
Drive/NotebookLM sync reminder, add a companion-app step:

> **5. Update The Hero's Book** (the `rpg_kids_companion` repo):
> 1. `cd C:\Users\micha\Documents\github\rpg_kids_companion`
> 2. `python tools/export_player_data.py --check` — it will list exactly what the
>    session added that needs a decision (new quests, items, spells, the session's
>    journal entry).
> 3. Author the kid text in `tools/kid_text.json` and the session entry in
>    `tools/journal.md` (2 to 4 short kid sentences, table-revealed facts only,
>    no em-dashes, no semicolons).
> 4. `python tools/export_player_data.py` — review the printed
>    "Secrets filter exclusions" list. Everything on it stays hidden from the
>    girls. If a table-revealed thing shows up there, fix the allow-list.
> 5. Bump `CACHE_VERSION` in `app/sw.js`, commit, push. The static host redeploys
>    from `main` automatically.

## 2. Conventions the export now depends on (already true today — keep them true)

These are the exact shapes the parser reads. They all hold in current canon, so
this is "do not break" rather than "change something":

- `house_rules.md` §3 hero table: 7 columns, hero name in bold, the
  `*(not yet at the table)*` marker on unjoined heroes.
- `house_rules.md` "### Ability text": `**Hero Name**` block headers with
  `- *Ability* (Type): ...` bullets, names matching the table's ability list.
- `house_rules.md` "### Unlocked Lima Spells": blocks starting
  `**<emoji> Spell Name** (Owner Hero). Card: ` followed by the card path in
  backticks. A spell listed here must also appear in the owner's
  `current_state.md` inventory row as `**Spell Name** spell card` (the export
  treats a mismatch as a canon sync bug and refuses to run).
- `current_state.md`: the `Party Resources` table with a `Gold` row (a number, or
  `❓ ...` while uncounted), the `Party Inventory` table with one row per hero
  plus `Party (shared)`, items separated by `·`, and the `Active Quests & Hooks`
  bullets starting with the quest name in bold.
- Session logs: `02_Session_Logs/session_NN_slug.md` with a first line of
  `# Session NN — Title`.

If any of these formats ever needs to change, change the parser in the companion
repo in the same sitting.

## 3. Optional, only if it ever feels natural

The kid-facing journal source currently lives in the companion repo
(`tools/journal.md`) so that canon needed no new files. If you would rather author
the journal entry during the canon wrap itself, it can move to
`02_Session_Logs/player_journal.md` in canon later. That is a one-line path change
in the export script. Nothing else would move: `kid_text.json` is presentation
copy (icons, colors, kid phrasing), not campaign fact, so it belongs in the app
repo either way.
