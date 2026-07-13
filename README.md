# The Hero's Book

A companion app for the Lima Clan tabletop campaign (see the private `rpg_kids` repo). It runs on the girls' Amazon Fire tablets and replaces the growing pile of paper: character sheets, spell and item cards, gold tracking, and quest notes. It is **not** a way to play the game. The game stays at the table with dice and printed loot cards. This is each hero's storybook and satchel.

## Design Pillars

1. **The canon repo is the only source of truth.** This app never invents or stores campaign facts. A build step reads the canon Markdown in `rpg_kids` and emits `app/data/player_data.json`. The app is a viewer over that file.
2. **The export is the secrets filter.** Only content the players have actually discovered at the table (per `current_state.md`) may appear in the data file. Nothing about unrevealed mysteries ships to a tablet, ever. Example: the Moon-Stone quest exists in canon but had not been played when v0 was built, so it is absent from the mock data.
3. **Reading is a feature.** The girls are 5 and 7 and this game is the younger one's reading incentive. Text appears everywhere, in short kid-sized sentences, always paired with an icon or art so nobody is ever blocked. A read-aloud button (Web Speech API) assists without replacing reading.
4. **Hybrid physical.** New loot is still handed over as a printed card at the table for the reward moment. It appears in the app after the between-session update.
5. **Light tracking only.** Tappable hearts (the Hero Kids three-step track: Bruised, Hurt, KO) and local state per tablet. No servers, no accounts, no sync. If a tablet loses its state, nothing of value is lost.

## App Layout

Each tablet remembers its girl's hero and opens straight to it.

| Tab | Contents |
| :-- | :-- |
| 🦸 My Hero | Banner art, hearts, dice stats, powers, spells, personal items |
| 👧 Family | Her sisters' heroes and spells (Night Armor shows as joining soon) |
| 🐾 Pets | Placeholder until the pets are chosen and named at the table |
| 💰 Treasure | Party gold and shared items, plus her own things |
| 📖 Our Story | Kid-readable journal of past games and the active quest list |

A grown-up corner (press and hold the gear for about a second) resets hearts, switches the tablet's hero, and forces an update check.

## Tech

Plain HTML, CSS, and vanilla JS. No framework, no build step, no dependencies. Offline-first PWA via a service worker, so a WiFi hiccup at the table changes nothing. Everything in `app/` is the deployable site.

- `app/index.html`, `app/css/app.css`, `app/js/app.js` — the app
- `app/data/player_data.json` — generated player-facing data (see The Export below; do not edit by hand)
- `app/art/` — renders copied from the canon repo by the export script
- `app/icons/` — the SVG source plus generated PNGs (192, 512, 512-maskable) for older Silk versions
- `app/sw.js` — offline cache. **Bump `CACHE_VERSION` on every deploy** so tablets refresh.
- `tools/` — the export script and its sources (see `tools/README.md`)

### Run locally

```
cd app
python -m http.server 8080
```

Then open http://localhost:8080 (a served origin is required, `file://` will not load the JSON).

### Picking up on another machine

1. Clone this repo and the private `rpg_kids` canon repo.
2. Python 3.8+ is the only requirement. The app and the export use nothing but the
   standard library: no packages, no npm, nothing to install.
3. The export script assumes the canon checkout is at
   `C:\Users\micha\Documents\github\rpg_kids`. If it lives elsewhere, pass
   `--canon-root <path>` or edit `DEFAULT_CANON_ROOT` at the top of
   `tools/export_player_data.py`.
4. Run the local server (above) and `python tools/export_player_data.py --check`
   to confirm both repos are healthy before doing anything else.

### Deploy

Live on Cloudflare Pages, connected to this private repo: no build command, build
output directory `app/`, and every push to `main` deploys automatically. Setup
history, tablet install steps, the every-deploy checklist, and troubleshooting are
in `docs/hosting.md`. Tablets install it from Silk via Add to Home Screen.

## The Export

`tools/export_player_data.py` reads the sibling `rpg_kids` checkout and generates `app/data/player_data.json` plus the art in `app/art/`. Canon supplies the facts, `tools/kid_text.json` is the kid-facing allow-list (rewrites, icons, art picks, hide/exclude decisions), and `tools/journal.md` holds the authored journal entries. The filter is default-closed: anything in canon without an explicit allow-list decision fails the export loudly instead of shipping. The full workflow lives in `tools/README.md`.

| App data | Canon source |
| :-- | :-- |
| Hero stats and ability text | `01_Campaign_Bible/house_rules.md` §3 |
| Spells and limits | `house_rules.md` Unlocked Lima Spells |
| Inventory, gold, quests | `01_Campaign_Bible/current_state.md` |
| Journal entries | `02_Session_Logs/` (kid-readable rewrites) |
| Art | `05_Asset_Pipeline/Final_Art/` |

Rules for the script (enforced, not aspirational): revealed-only content, kid-sized sentences, no em-dashes and no semicolons in any kid-facing text. The `rpg_kids` post-session wrap gains a final step: rerun the export, bump the service worker cache version, push — the proposal to carry into the canon repo is `docs/canon_repo_proposal.md`.

## Roadmap

- **v0 (done):** clickable mockup with mock data for all three heroes, deployable structure, offline-ready.
- **v1 (current):** export script done and mutation-tested, hosting live on Cloudflare Pages, PNG icons done. Remaining: read-aloud tested on the actual tablets, a fact-check pass on the three ported journal entries against the session logs, and the first real post-session export after Session 04.
- **v2/v3 ideas:** in-session puzzle and cipher mini-pages the GM can direct the girls to, pet pages once pets are canon, per-hero reading levels that grow with the reader.
