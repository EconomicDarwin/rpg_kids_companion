# Wrap profile: rpg_kids_companion

Read by the personal wrap skills, `wrap-session-personal` and `wrap-terminal-personal`, whose
canonical copies live in the `personal` repo's `.claude/skills/` and are installed at the user
level by that repo's `tools/install-wrap-skills.ps1`. The skills are the procedure. This file is
what is particular to this repo. Fixed headings, in this order: About this repo, Extra steps,
Documentation sweep, Sensitivity check, The gate, The narrow gate, Commit rules, The pick-up
prompt. No branch name, model name, or machine path here, so derive them at run time.

## About this repo

"The Hero's Book", the girls' companion app for the Lima Clan campaign. A plain HTML, CSS and
vanilla JS progressive web app with no framework, no build step and no dependencies, served from
`app/` and read on Amazon Fire tablets in Silk and on the girls' laptops in Edge or Chrome. It is
a viewer and light bookkeeper over `app/data/player_data.json`, never a way to play the game and
never a second source of truth.

**Two boundaries define this repo.** The canon repo `../rpg_kids` is **read-only** from here: read
its files, never run git there and never edit it, and never read its `00_Drafts/`. And
`tools/export_player_data.py` is **the secrets filter**, since only what the girls have already
discovered at the table may reach a tablet. This is also the one personal repo that publishes:
every push to `main` deploys `app/` to Cloudflare Pages automatically.

## Extra steps

1. **A push here is a deploy.** Treat the push as the release step, not an afterthought, and say
   so in the wrap report. Never push a half-finished screen because the wrap reached step 4.
2. **The cache bump travels with the deploy.** If anything under `app/` changed, `CACHE_VERSION`
   in `app/sw.js` must be bumped in the same push, or the tablets will show the old app and it
   will look like nothing happened.
3. **If canon moved, rerun the export** (`python tools/export_player_data.py`) so
   `app/data/player_data.json` matches, and record in your section which canon commit it reflects.
   The export fails loudly on any canon entity with no allow-list decision in
   `tools/kid_text.json`, and that default-closed behavior is the filter. Never weaken it to skip
   silently.

## Documentation sweep

- **`README.md`**: the full brief, and it is expected to stay accurate and current.
- **`CLAUDE.md`**: when a rule, a boundary, or a tech constraint changed.
- **`docs/hosting.md`**: when anything about the Cloudflare Pages setup, the deploy or the
  troubleshooting changed.
- **`tools/README.md`**: when the export's behavior, flags, or canon-root handling changed.
- **`tools/kid_text.json`**: new canon entities need an allow-list decision, and a decision is a
  deliberate act, so record new ones rather than letting the export stay red.
- **The schema contract**: if the shape of `player_data.json` changed, both the export and
  `app/js/app.js` change together, and the reason is written down.
- **Per-user memory**: entries that name workflows, paths, or facts this session changed.

Shared files, re-read before every edit: `README.md`, `tools/kid_text.json`.

**Open actions** go in this repo's README or issue list, never a new to-do file. Anything that
needs canon to change is written up as a proposal for the user to carry to `../rpg_kids`, because
this repo never edits canon.

## Sensitivity check

- **The export is the filter, and it is the whole game.** Nothing may reach `player_data.json`,
  `app/art/`, or any screen unless the girls have discovered it at the table, gated by canon's
  `01_Campaign_Bible/current_state.md`. GM mysteries stay in canon. When in doubt, leave it out
  and flag it.
- **This repo is public-facing by deploy.** Anything committed here reaches the internet through
  Cloudflare Pages, so no GM secret, no real family detail, and nothing from a work repo.
- **Kid-facing writing style:** short kid-sized sentences, no em dashes, no en dashes, no
  semicolons. The readers are 7 and 5, and the younger one is learning, so the app is her reading
  incentive.
- **Never read `../rpg_kids/00_Drafts/`**, which is unapproved brainstorming.

## The gate

- **The export runs clean:** `python tools/export_player_data.py` completes with no allow-list
  failure, and the diff to `app/data/player_data.json` is what you expect.
- **The app serves and renders:** `cd app` then `python -m http.server 8080`, and check that
  every hero tab renders, Treasure shows party items, Our Story lists one entry per played
  session, and Our World lists the people the girls have met. A served origin is required, since
  `file://` loads neither the JSON nor the service worker. Headless Chrome is fine for the smoke
  check.
- **Both widths:** check the tablet width and a screen 900px or wider, since the laptop layout
  comes from one media query at the bottom of `app/css/app.css`.
- **The cache bump** is present when `app/` changed.
- **No build step and no dependency** was introduced in `app/`. The export's use of Pillow is the
  one allowed exception, and nothing that ships to a tablet may need a build.
- **Writing register** on kid-facing text and docs, and the secrets filter on everything staged.

## The narrow gate

| Changed | Check |
|---|---|
| `app/` (any file) | serve and render both widths, `CACHE_VERSION` bumped, no dependency added |
| `app/data/player_data.json` or `tools/export_player_data.py` | export runs clean, schema contract holds on both sides, secrets filter reviewed |
| `tools/kid_text.json` | every new canon entity has a deliberate decision, kid-facing register |
| docs only (`README.md`, `docs/`, `CLAUDE.md`) | writing register, and nothing secret quoted from canon |
| memory files only | no check, state that |

## Commit rules

- **A terminal wrap never commits or pushes.**
- Commit by path, never `git add -A` and never `commit -a`. One commit per coherent chunk, for
  example the export separately from a screen.
- **The deploy rule:** an `app/` change, its cache bump, and a regenerated `player_data.json` go
  in the same push, because a partial push deploys a partial app.
- Push only when the user asked, and say in the report that the push deployed.
- Message: a one-line summary, then grouped bullets saying what changed and how it was verified,
  ending with the trailer the session's operating instructions specify. Never hardcode a model
  name, and never put a canon secret in a commit message.

## The pick-up prompt

1. One line: resuming rpg_kids_companion on the branch actually checked out (read it, do not
   assume). Read `CLAUDE.md` and `README.md`, and `tools/README.md` for export work.
2. The standing rules, one line each: canon at `../rpg_kids` is read-only and its `00_Drafts/` is
   off limits, the export is the secrets filter and stays default-closed, kid-sized sentences
   with no dashes and no semicolons, no framework and no build step, and a push to `main` is a
   deploy that needs its cache bump.
3. "Verify the checkout first": `git status` clean, `git pull` current, the export runs clean,
   and the app serves locally.
4. Three to six bullets of where we left off: the last commits' headlines, whether the deployed
   site matches the working tree, which canon commit the current export reflects, and the agreed
   next steps.
5. "Then report status and wait for direction."
