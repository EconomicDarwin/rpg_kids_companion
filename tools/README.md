# The export pipeline

`export_player_data.py` turns canon (the read-only `rpg_kids` repo) into
`app/data/player_data.json` plus the art in `app/art/`. It is the secrets filter.

## The three sources

| File | Role |
| :-- | :-- |
| canon repo (`C:\Users\micha\Documents\github\rpg_kids`) | The facts: heroes, stats, ability names and types, unlocked spells, inventory, gold, quests, session logs. Read-only. |
| `tools/kid_text.json` | The allow-list: what ships and how it reads for the kids. Kid rewrites of ability text, item and quest descriptions, icons, accents, banner art picks. |
| `tools/journal.md` | Authored kid-facing journal entries, one per played session. |

The design is default-closed. Every hero, quest, inventory item, spell, and session
log found in canon must have a matching entry here, an `excludedHeroes` reason, or a
quest `"hidden": true` marker. Anything undecided fails the export with a specific
error. Anything here that canon no longer backs also fails (stale entry). Kid-facing
text containing an em-dash, en-dash, semicolon, or `❓` fails. Never weaken any of
this to "skip silently" — silent skipping is how a secret leaks or a reward goes
missing.

## After each session (the update workflow)

1. Finish the canon repo's own wrap (session log written, `current_state.md` updated).
2. Run `python tools/export_player_data.py --check` here. It will fail loudly,
   listing exactly what is new and undecided.
3. For each error: author kid text in `kid_text.json`, add the session's entry to
   `journal.md` (2 to 4 short kid sentences, table-revealed facts only), or mark a
   quest hidden with a reason.
4. Run `python tools/export_player_data.py` for real. Review the
   "Secrets filter exclusions" list it prints. That list is the things being kept
   from the kids. If something revealed at the table is on it, fix the allow-list.
5. Bump `CACHE_VERSION` in `app/sw.js`, commit, push. See `docs/hosting.md`.

## Flags

- `--check` — validate and report, write nothing.
- `--canon-root PATH` — point at a different canon checkout (used by tests).
- `--prune-art` — delete files in `app/art/` the export no longer needs
  (otherwise leftovers are an error, because everything in `app/` ships).

## Known caretaking notes

- Kid text is authored, so counts inside it can go stale (example: the Star-Seeds
  text says how many uses are left). When canon changes a number, update the kid
  text by hand. The stale-entry checks only catch renames and removals, not counts.
- The journal is a rewrite, never a copy. GM logs contain unrevealed context.
