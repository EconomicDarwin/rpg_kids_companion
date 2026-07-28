# Proposal: changes to carry over to the rpg_kids canon repo

> **Status as of 2026-07-27.**
> - **Section 1 (the wrap step): still open.** Checked directly: canon's
>   `.claude/skills/wrap-session/SKILL.md` has no companion-app step. Sessions 04
>   and 05 both landed without one, and the export sat broken in between. That is
>   the cost of the missing step, not an argument against it.
> - **Section 2 (formats): partly overtaken.** Session 04 changed two of the exact
>   shapes this asked to keep stable. The export was taught both, and the list below
>   is updated to match what canon actually does now.
> - **Section 3 (Roger): applied, keep for the record.** Canon now records both
>   rescues in all four files.

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
- `current_state.md`: the `Party Inventory` table with one row per hero plus
  `Party (shared)`, items separated by `·`, and the `Active Quests & Hooks`
  bullets starting with the quest name in bold, optionally struck through with
  `~~` once finished.
  *(Session 04 replaced the single `Gold` row in `Party Resources` with per-hero
  "Gold & Gems" rows. The app no longer reads gold at all, by choice: the girls
  handle real coins and gems at the table and it is playing well. `kid_text.json`
  records that as `"goldTracking": false`. Flip it to `true` and the export starts
  requiring a parseable gold figure again.)*
- Session logs: `02_Session_Logs/session_NN_slug.md` with a first line of
  `# Session NN — Title`.

If any of these formats ever needs to change, change the parser in the companion
repo in the same sitting.

## 3. Correction: Roger is rescued twice, not once — APPLIED

**Done on 2026-07-27.** All four files below now record both rescues, and
`master_lore.md` even took the "two rescues in three sessions may be answer enough"
note about his unestablished role. Kept here as the record of why.

Confirmed with Michael on 2026-07-26 while fact-checking the player journal. The
girls rescue Roger **in Basement o' Rats (session 1, in the Block and Tackle's own
basement) and again from under the chandelier in Fire in Rivenshore (session 3)**.
Canon currently records only the second rescue, and describes it as the single
reason for Odbert's devotion.

Four files say "rescued once" and would each want a mention of both:

- `02_Session_Logs/session_01_the_secret_of_the_lima_clan.md` — the Basement o' Rats
  line does not mention Roger at all. It is where the first rescue belongs, and the
  basement is the Block and Tackle's.
- `01_Campaign_Bible/master_lore.md` (Roger entry) — "Rescued by the girls from
  under a chandelier during the Fire in Rivenshore."
- `03_Locations_and_NPCs/rivenshore.md` (Block and Tackle key NPCs) — same wording.
- `06_Maps/rivenshore_map.html` (stop 10) — "Roger (rescued from the fire)."

Roger's role at the tavern is still flagged as unestablished in two of those files.
Two rescues in three sessions is arguably its own answer.

## 4. Optional, only if it ever feels natural

The kid-facing journal source currently lives in the companion repo
(`tools/journal.md`) so that canon needed no new files. If you would rather author
the journal entry during the canon wrap itself, it can move to
`02_Session_Logs/player_journal.md` in canon later. That is a one-line path change
in the export script. Nothing else would move: `kid_text.json` is presentation
copy (icons, colors, kid phrasing), not campaign fact, so it belongs in the app
repo either way.
