# The export pipeline

`export_player_data.py` turns canon (the read-only `rpg_kids` repo) into
`app/data/player_data.json` plus the art in `app/art/`. It is the secrets filter.

Needs Python 3.8+ and Pillow (`pip install Pillow`).

## The three sources

| File | Role |
| :-- | :-- |
| canon repo (`C:\Users\micha\Documents\github\rpg_kids`) | The facts: heroes, stats, ability names and types, unlocked spells, inventory, gold, quests, session logs. Read-only. |
| `tools/kid_text.json` | The allow-list: what ships and how it reads for the kids. Kid rewrites of ability text, item and quest descriptions, icons, accents, banner art picks. |
| `tools/journal.md` | Authored kid-facing journal entries, one per played session, each able to name one picture. |

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

## Art

Canon art is drawn for print: mostly 2816x1536 PNGs at 7-9 MB, saved RGBA even
though every pixel is opaque. The export refits each shipped picture to 1600px and
re-encodes it (JPEG at quality 82, or PNG if the alpha channel is genuinely used),
which lands around 2% of the original size. 1600px keeps the full-screen lightbox
crisp on the highest resolution Fire tablet. `sw.js` caches every shipped file
before offline mode works, so this is the difference between a 37 MB first load and
a 2 MB one.

Two consequences worth remembering:

- Shipped filenames end in `.jpg` even though canon holds `.png`. That is why
  `kid_text.json` and `journal.md` name the canon path, never the shipped one.
- Re-encoding is deterministic, so a rerun that changes nothing rewrites nothing.

**Pictures are an allow-list decision like any other.** Canon art is drawn for the
GM and can show things the girls have not learned yet, so look at the image before
naming it. Text can be linted; a drawing cannot.

The worked example is `equipment/odberts_box_contents.png`. The torn letter in it
plainly reads "the glyph leads to the moon-stone," so through Session 03 it was
held back and journal entry 2 shipped with no picture at all. Moira revealed the
Moon-Stone in Session 04, and only then did the picture go in. Session 05 is the
live case: Beats 3 and 4 are unplayed, so `scenes/moon_stone_chamber_sisters.png`,
`sky_saver_lifts_moon_stone.png`, `rainbow_with_clouds_lifts_moon_stone.png`,
`locations/aethelia_music_box.png` and `aethelia_star_seed_camp.png` all exist in
canon and none of them may ship yet.

## Known caretaking notes

- Kid text is authored, so counts inside it can go stale (example: the Star-Seeds
  text says how many uses are left). When canon changes a number, update the kid
  text by hand. The stale-entry checks only catch renames and removals, not counts.
- The journal is a rewrite, never a copy. GM logs contain unrevealed context.
