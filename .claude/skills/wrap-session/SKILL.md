---
name: wrap-session
description: End-of-session wrap for the rpg_kids_companion repo — sync the export against canon if it moved, sweep documentation current, verify the app locally, commit and push, then emit a pick-up prompt for a fresh session. Use when the user says "wrap up", "update docs, commit and push", "give me a handoff prompt", or is ending a work session.
---

# Wrap the session

Do these steps **in order**. Report each step's result plainly; never skip the export check when
canon moved. This is a small static-site repo with no test suite — the "gate" here is the
secrets-filter export check plus a manual smoke test.

## 1. Sync against canon (only if campaign data moved this session)

The sibling canon repo (`C:\Users\micha\Documents\github\rpg_kids`) is read-only from here —
never edit it or run git there. If a game session was logged or canon otherwise changed since the
last wrap:

1. `python tools/export_player_data.py --check` from the repo root — lists exactly what's new and
   undecided (new heroes, quests, items, spells, or a session missing its journal entry). It fails
   loudly by design; that default-closed behavior is the secrets filter.
2. For each item it flags: author kid text in `tools/kid_text.json` (the allow-list), add the
   session's entry to `tools/journal.md` (heading exactly `## Session N — Title`, 2 to 4 short
   kid-sized sentences, table-revealed facts only, no em-dashes, no semicolons), or mark a quest
   hidden with a reason if it shouldn't ship yet.
3. `python tools/export_player_data.py` for real — review the printed "Secrets filter exclusions"
   list. Everything on it stays hidden from the girls; if something revealed at the table shows up
   there, fix the allow-list rather than accepting it.

If no campaign data moved (pure app/code/docs work), skip to step 2.

## 2. Documentation sweep

Bring every document the session's changes touch up to date (most should already be current if
the work followed the repo rules — this is the catch-up pass):

- **Root `CLAUDE.md`** — tech constraints or workflow notes if this session changed how the app,
  export, or deploy works.
- **`README.md`** — the Roadmap section (v0/v1/v2 items) if scope moved; the App Layout table if
  tabs changed; the Export Contract table if the canon-to-app field mapping changed.
- **`docs/hosting.md`** — if the deploy process, hosting provider, or the every-deploy checklist
  changed.
- **`docs/canon_repo_proposal.md`** — a standing proposal to add a companion-app reminder step to
  the canon repo's own wrap-session skill. If the user says that's been applied over in `rpg_kids`,
  note it resolved here; otherwise leave it open.
- **`tools/README.md`** — if the export pipeline's rules, flags, or caretaking notes changed.
- **Per-user memory** (`~/.claude/.../memory/`) — update entries naming this repo's paths or
  workflow if this session changed them.

Kid-facing style check while sweeping (repo rule 2): short kid-sized sentences, no em-dashes, no
semicolons, in anything that ships to a tablet.

## 3. Verify locally

No automated test suite exists; this is a manual smoke check:

```
cd app
python -m http.server 8080
```

Open http://localhost:8080 — a served origin is required, `file://` will not load the JSON or
register the service worker. Confirm: all three hero tabs render, Treasure shows party items, Our
Story lists one journal entry per played session with nothing stale or missing. If `app/js/app.js`
or `player_data.json`'s shape changed this session, actually click through the tabs — the schema
contract between them is not type-checked anywhere.

If any file under `app/` changed (HTML, CSS, JS, data, or art), **bump `CACHE_VERSION` in
`app/sw.js`** — a deploy without the bump looks like nothing changed on the tablets.

## 4. Commit and push

- Check `git status` for surprises first: files you didn't change, leftover `app/art/` files an
  export with `--prune-art` would have removed, anything that shouldn't ship.
- One commit per coherent chunk when separable (a canon/export sync, app code, docs); one
  structured commit when they interleave. Message: a one-line summary, then grouped bullets (what
  + how verified), ending with:

  ```
  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```
- `git push` and confirm `origin/main` advanced.
- **Remind the user of the deploy step** — every push to `main` triggers a Cloudflare Pages /
  Netlify redeploy automatically, but each tablet still needs the grown-up-corner "force an update
  check" once the deploy shows Success in the dashboard. Claude cannot do this part; say it
  explicitly every wrap.

## 5. The pick-up prompt

Emit a fenced block the user can paste into a fresh session. Build it from the CURRENT state — do
not reuse a stale template. It must contain:

1. The one-line orientation: resuming rpg_kids_companion on branch `main`; the repo is
   self-sufficient — read the root `CLAUDE.md` and `README.md`. Canon lives at the sibling
   `rpg_kids` repo (read-only from here — never edit it or run git there).
2. The standing rules reminder: the export is the secrets filter, default-closed, never weaken to
   "skip silently"; kid-facing text is short, no em-dashes, no semicolons; `app/` is the deployable
   site as-is with no build step; bump `CACHE_VERSION` on every deploy that touches `app/`.
3. "Verify the checkout first": `cd app && python -m http.server 8080` plus the three-tab smoke
   check, and `python tools/export_player_data.py --check` if canon may have moved since.
4. A 3-6 bullet "where we left off": the last commits' headlines, anything in flight (an
   undecided allow-list entry, an unwritten journal session, a hosting step not yet done), and the
   agreed next steps.
5. "Then report status and wait for direction."
