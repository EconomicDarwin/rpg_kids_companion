#!/usr/bin/env python3
"""Export app/data/player_data.json from the rpg_kids canon repo.

Design: default-closed. The canon repo says WHAT exists (heroes, stats, ability
names, spells, inventory, quests, session logs). tools/kid_text.json is the
allow-list that says what ships to the tablets and how it reads for the kids.
tools/journal.md holds the authored kid-facing journal entries.

Anything found in canon that has no explicit allow-list decision (an entry, an
"excludedHeroes" reason, or a quest marked "hidden") FAILS the export. Anything
in the allow-list no longer backed by canon also fails (stale entry). That
default-closed behavior is the secrets filter. Never weaken it to skip silently.

The canon repo is READ-ONLY from here. This script must never write into it.

Usage:
  python tools/export_player_data.py [--canon-root PATH] [--check] [--prune-art]

  --check      validate everything and report what would change, write nothing
  --prune-art  delete files in app/art/ that the export no longer needs
"""

from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
import sys
from pathlib import Path

DEFAULT_CANON_ROOT = Path(r"C:\Users\micha\Documents\github\rpg_kids")

REPO_ROOT = Path(__file__).resolve().parent.parent
KID_TEXT_PATH = REPO_ROOT / "tools" / "kid_text.json"
JOURNAL_PATH = REPO_ROOT / "tools" / "journal.md"
OUT_PATH = REPO_ROOT / "app" / "data" / "player_data.json"
ART_DIR = REPO_ROOT / "app" / "art"

FINAL_ART_REL = Path("05_Asset_Pipeline/Final_Art")

GENERATED_NOTE = (
    "GENERATED FILE. Run tools/export_player_data.py to regenerate. "
    "Do not edit by hand."
)

# Characters banned from kid-facing text (style rule: short sentences,
# no em-dashes, no semicolons; ❓ means unexported GM TODO leaked through).
BANNED_CHARS = {"—": "em-dash", "–": "en-dash", ";": "semicolon", "❓": "GM TODO marker"}


class Exporter:
    def __init__(self, canon_root: Path):
        self.canon = canon_root
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.excluded: list[str] = []  # secrets-filter decisions, reported on success

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    # ---------- small helpers ----------

    def read_canon(self, rel: str) -> str | None:
        p = self.canon / rel
        if not p.is_file():
            self.err(f"Canon file missing: {p}")
            return None
        return p.read_text(encoding="utf-8")

    @staticmethod
    def section(md: str, level: int, keyword: str) -> str | None:
        """Return the body of the first heading of `level` whose text contains
        keyword, up to the next heading of the same or higher level."""
        hashes = "#" * level
        pat = re.compile(rf"(?m)^{hashes}(?!#)[^\n]*{re.escape(keyword)}[^\n]*\n")
        m = pat.search(md)
        if not m:
            return None
        rest = md[m.end():]
        stop = re.search(rf"(?m)^#{{1,{level}}}(?!#)\s", rest)
        return rest[: stop.start()] if stop else rest

    @staticmethod
    def table_rows(body: str) -> list[list[str]]:
        """Parse markdown table rows (skipping header and alignment lines)."""
        rows = []
        for line in body.splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue  # alignment row
            rows.append(cells)
        return rows[1:] if rows else []  # drop header row

    @staticmethod
    def strip_md(text: str) -> str:
        return re.sub(r"\*+", "", text).strip()

    @staticmethod
    def strip_trailing_paren(text: str) -> str:
        return re.sub(r"\s*\([^)]*\)\s*$", "", text).strip()

    def lint_kid(self, text: str, where: str) -> None:
        for ch, name in BANNED_CHARS.items():
            if ch in text:
                self.err(f"Kid-style violation ({name}) in {where}: {text!r}")

    # ---------- canon parsing ----------

    def parse_house_rules(self):
        """Returns (heroes, spells).
        heroes: {name: {class, stats, joined, abilities: {name: type}}}
        spells: {spell_name: {icon, owner, card (canon-relative path)}}
        """
        md = self.read_canon("01_Campaign_Bible/house_rules.md")
        if md is None:
            return {}, {}

        sec3 = self.section(md, 2, "The Heroes")
        if sec3 is None:
            self.err("house_rules.md: section '## 3. The Heroes' not found")
            return {}, {}

        # Hero table lives before the first ### subsection.
        table_part = sec3.split("\n###", 1)[0]
        heroes: dict[str, dict] = {}
        for cells in self.table_rows(table_part):
            if len(cells) != 7:
                self.err(f"house_rules.md hero table: expected 7 columns, got {len(cells)}: {cells}")
                continue
            m = re.search(r"\*\*(.+?)\*\*", cells[0])
            if not m:
                self.err(f"house_rules.md hero table: no bold hero name in {cells[0]!r}")
                continue
            name = m.group(1)
            stats = {}
            for key, cell in zip(("melee", "ranged", "magic", "armor"), cells[2:6]):
                try:
                    stats[key] = int(self.strip_md(cell))
                except ValueError:
                    self.err(f"house_rules.md: bad {key} value {cell!r} for {name}")
                    stats[key] = 0
            heroes[name] = {
                "class": self.strip_md(cells[1]),
                "stats": stats,
                "joined": "not yet at the table" not in cells[0].lower(),
                "abilities": {},
                "ability_order": [a.strip() for a in cells[6].split("·")],
            }

        # Ability text subsection: type per ability, grouped under **Hero** lines.
        ab = self.section(md, 3, "Ability text")
        if ab is None:
            self.err("house_rules.md: section '### Ability text' not found")
        else:
            current = None
            for line in ab.splitlines():
                h = re.match(r"^\*\*(.+?)\*\*", line)
                if h:
                    current = h.group(1)
                    continue
                b = re.match(r"^- \*(.+?)\* \(([^),]+)(?:,[^)]*)?\):", line)
                if b:
                    if current is None or current not in heroes:
                        self.err(f"house_rules.md ability text: bullet outside a known hero block: {line!r}")
                    else:
                        heroes[current]["abilities"][b.group(1)] = b.group(2).strip()

        # Cross-check: table ability list == ability-text names, per hero.
        for name, h in heroes.items():
            listed = set(h["ability_order"])
            detailed = set(h["abilities"])
            if listed != detailed:
                self.err(
                    f"house_rules.md: ability mismatch for {name}: "
                    f"table lists {sorted(listed)}, ability text has {sorted(detailed)}"
                )

        # Unlocked spells.
        spells: dict[str, dict] = {}
        sp = self.section(md, 3, "Unlocked Lima Spells")
        if sp is None:
            self.err("house_rules.md: section '### Unlocked Lima Spells' not found")
        else:
            for m in re.finditer(
                r"(?m)^\*\*(\S+)\s+(.+?)\*\*\s*\((.+?)\)\.\s*Card:\s*`([^`]+)`", sp
            ):
                icon, sname, owner, card = m.groups()
                spells[sname] = {"icon": icon, "owner": owner, "card": card}
            if not spells:
                self.err("house_rules.md: 'Unlocked Lima Spells' section has no parseable spell blocks")
        return heroes, spells

    def parse_current_state(self):
        """Returns (gold, inventory, quests).
        gold: int | None ("unknown, count at table") — parse failure is an error.
        inventory: {owner: [item strings]} with owner 'Party (shared)' for the party row.
        quests: [(name, raw_line)] in canon order.
        """
        md = self.read_canon("01_Campaign_Bible/current_state.md")
        if md is None:
            return None, {}, []

        gold = None
        res = self.section(md, 2, "Party Resources")
        if res is None:
            self.err("current_state.md: section 'Party Resources' not found")
        else:
            gold_cell = None
            for cells in self.table_rows(res):
                if len(cells) >= 2 and self.strip_md(cells[0]).lower() == "gold":
                    gold_cell = cells[1]
            if gold_cell is None:
                self.err("current_state.md: no Gold row in Party Resources table")
            elif "❓" in gold_cell:
                gold = None  # explicitly unknown, expected state
            else:
                m = re.fullmatch(r"(\d+)(?:\s*gold)?", self.strip_md(gold_cell), re.I)
                if m:
                    gold = int(m.group(1))
                else:
                    self.err(f"current_state.md: cannot parse Gold amount {gold_cell!r}")

        inventory: dict[str, list[str]] = {}
        inv = self.section(md, 2, "Party Inventory")
        if inv is None:
            self.err("current_state.md: section 'Party Inventory' not found")
        else:
            for cells in self.table_rows(inv):
                if len(cells) != 2:
                    self.err(f"current_state.md inventory: expected 2 columns, got {cells}")
                    continue
                owner = self.strip_md(cells[0])
                items = [t.strip() for t in cells[1].split("·") if t.strip()]
                inventory[owner] = items
            if not inventory:
                self.err("current_state.md: Party Inventory table is empty")

        quests: list[tuple[str, str]] = []
        q = self.section(md, 2, "Active Quests")
        if q is None:
            self.err("current_state.md: section 'Active Quests' not found")
        else:
            for line in q.splitlines():
                line = line.strip()
                if not line.startswith("- "):
                    continue
                m = re.match(r"^- \*\*(.+?)\*\*", line)
                if m:
                    quests.append((m.group(1), line))
                else:
                    self.err(f"current_state.md quests: bullet without a bold quest name: {line!r}")
            if not quests:
                self.err("current_state.md: 'Active Quests' section has no quest bullets")
        return gold, inventory, quests

    def parse_session_logs(self) -> dict[int, str]:
        """Returns {session number: GM title} from 02_Session_Logs/session_*.md."""
        logs_dir = self.canon / "02_Session_Logs"
        if not logs_dir.is_dir():
            self.err(f"Canon session log directory missing: {logs_dir}")
            return {}
        logs: dict[int, str] = {}
        for p in sorted(logs_dir.glob("session_*.md")):
            head = p.read_text(encoding="utf-8").splitlines()[0] if p.stat().st_size else ""
            m = re.match(r"#\s*Session\s+(\d+)\s+—\s+(.+)", head)
            if not m:
                self.err(f"{p.name}: first line is not '# Session NN — Title': {head!r}")
                continue
            n = int(m.group(1))
            if n in logs:
                self.err(f"Duplicate canon session log for session {n}")
            logs[n] = m.group(2).strip()
        if not logs:
            self.err(f"No parseable session logs found in {logs_dir}")
        return logs

    def parse_journal(self) -> dict[int, dict]:
        """Returns {session number: {title, text}} from tools/journal.md."""
        if not JOURNAL_PATH.is_file():
            self.err(f"Journal source missing: {JOURNAL_PATH}")
            return {}
        md = JOURNAL_PATH.read_text(encoding="utf-8")
        entries: dict[int, dict] = {}
        parts = re.split(r"(?m)^## Session (\d+) — (.+)$", md)
        # parts = [preamble, num, title, body, num, title, body, ...]
        for i in range(1, len(parts), 3):
            n, title, body = int(parts[i]), parts[i + 1].strip(), parts[i + 2]
            text = " ".join(l.strip() for l in body.splitlines() if l.strip())
            if n in entries:
                self.err(f"journal.md: duplicate entry for session {n}")
            if not text:
                self.err(f"journal.md: session {n} has an empty entry")
                continue
            entries[n] = {"title": title, "text": text}
            sentences = len(re.findall(r"[.!?]", text))
            if not 2 <= sentences <= 5:
                self.warn(
                    f"journal.md session {n}: {sentences} sentences "
                    f"(aim for 2-4 short kid-sized sentences)"
                )
        return entries

    # ---------- assembly ----------

    def build(self, overlay: dict) -> tuple[dict | None, dict[str, Path]]:
        """Returns (player_data, art_jobs). art_jobs: {dest basename: source abs path}."""
        canon_heroes, canon_spells = self.parse_house_rules()
        gold, inventory, canon_quests = self.parse_current_state()
        logs = self.parse_session_logs()
        journal = self.parse_journal()
        art_jobs: dict[str, Path] = {}

        def add_art(rel_to_final_art: str, where: str) -> str | None:
            src = self.canon / FINAL_ART_REL / rel_to_final_art
            dest = Path(rel_to_final_art).name
            if not src.is_file():
                self.err(f"Art file missing in canon for {where}: {src}")
                return None
            if dest in art_jobs and art_jobs[dest] != src:
                self.err(f"Art name collision: {dest} wanted from both {art_jobs[dest]} and {src}")
                return None
            art_jobs[dest] = src
            return f"art/{dest}"

        # --- heroes: overlay is the allow-list, canon is the fact source ---
        overlay_heroes = {h["canonName"]: h for h in overlay["heroes"]}
        excluded_heroes = overlay.get("excludedHeroes", {})
        for name in canon_heroes:
            if name not in overlay_heroes and name not in excluded_heroes:
                self.err(
                    f"Canon hero {name!r} has no allow-list decision. Add a heroes "
                    f"entry or an excludedHeroes reason in tools/kid_text.json."
                )
        for name in overlay_heroes:
            if name not in canon_heroes:
                self.err(f"kid_text.json hero {name!r} not found in the canon hero table (stale?)")
        for name, reason in excluded_heroes.items():
            if name not in canon_heroes:
                self.err(f"kid_text.json excludedHeroes entry {name!r} not found in canon (stale?)")
            else:
                self.excluded.append(f"hero {name!r}: {reason}")

        # Spells: 'Unlocked' in house_rules must be confirmed handed out by the
        # inventory in current_state (the revealed gate). Any mismatch is a canon
        # sync bug and fails the export.
        spell_cards_held: dict[str, set[str]] = {}
        for owner, items in inventory.items():
            for raw in items:
                m = re.match(r"^(.+?) spell card$", self.strip_md(raw))
                if m:
                    spell_cards_held.setdefault(owner, set()).add(m.group(1))
        for sname, sp in canon_spells.items():
            if sp["owner"] not in canon_heroes:
                self.err(f"Spell {sname!r}: owner {sp['owner']!r} is not in the canon hero table")
            elif sname not in spell_cards_held.get(sp["owner"], set()):
                self.err(
                    f"Spell {sname!r} is 'Unlocked' in house_rules.md but not in "
                    f"{sp['owner']}'s current_state.md inventory. Reconcile canon first."
                )
        for owner, names in spell_cards_held.items():
            for sname in names:
                if sname not in canon_spells:
                    self.err(
                        f"{owner} holds spell card {sname!r} but house_rules.md has no "
                        f"'Unlocked Lima Spells' entry for it."
                    )

        heroes_out = []
        for oh in overlay["heroes"]:
            name = oh["canonName"]
            if name not in canon_heroes:
                continue
            ch = canon_heroes[name]

            # joined: house_rules flag, cross-checked against the inventory row
            inv_row = inventory.get(name, [])
            inv_says_not_joined = any("not yet joined" in self.strip_md(t) for t in inv_row)
            if ch["joined"] and inv_says_not_joined:
                self.err(f"{name}: house_rules says at the table, current_state inventory says not joined")

            abilities_out = []
            for aname in ch["ability_order"]:
                ov = oh["abilities"].get(aname)
                if ov is None:
                    self.err(
                        f"{name}: canon ability {aname!r} has no kid text in kid_text.json. "
                        f"Author it (or this ability cannot ship)."
                    )
                    continue
                self.lint_kid(ov["text"], f"{name} ability {aname!r}")
                abilities_out.append(
                    {"icon": ov["icon"], "name": aname, "type": ch["abilities"].get(aname, ""), "text": ov["text"]}
                )
            for aname in oh["abilities"]:
                if aname not in ch["abilities"]:
                    self.err(f"kid_text.json: {name} ability {aname!r} not found in canon (stale?)")

            spells_out = []
            for sname, sp in canon_spells.items():
                if sp["owner"] != name:
                    continue
                ov = oh["spells"].get(sname)
                if ov is None:
                    self.err(f"{name}: canon spell {sname!r} has no kid text in kid_text.json.")
                    continue
                card = sp["card"]
                prefix = FINAL_ART_REL.as_posix() + "/"
                if not card.startswith(prefix):
                    self.err(f"Spell {sname!r}: card path {card!r} is not under {prefix}")
                    art_ref = None
                else:
                    art_ref = add_art(card[len(prefix):], f"spell {sname!r}")
                self.lint_kid(ov["text"], f"spell {sname!r} text")
                self.lint_kid(ov["limit"], f"spell {sname!r} limit")
                spells_out.append(
                    {"name": sname, "icon": sp["icon"], "art": art_ref, "text": ov["text"], "limit": ov["limit"]}
                )
            for sname in oh["spells"]:
                if canon_spells.get(sname, {}).get("owner") != name:
                    self.err(f"kid_text.json: {name} spell {sname!r} not found in canon for her (stale?)")

            items_out = []
            seen_item_keys = []
            for raw in inv_row:
                clean = self.strip_md(raw)
                if clean.startswith("—") or "not yet joined" in clean:
                    continue
                if re.match(r"^(.+?) spell card$", clean):
                    continue  # rendered via spells above
                key = self.strip_trailing_paren(clean)
                seen_item_keys.append(key)
                ov = oh["items"].get(key)
                if ov is None:
                    self.err(
                        f"{name} carries {clean!r} (key {key!r}) with no kid_text.json entry. "
                        f"Author it or it cannot ship."
                    )
                    continue
                self.lint_kid(ov["text"], f"{name} item {key!r}")
                item = {"icon": ov["icon"], "name": ov.get("name", key)}
                if ov.get("art"):
                    art_ref = add_art(ov["art"], f"item {key!r}")
                    if art_ref:
                        item["art"] = art_ref
                item["text"] = ov["text"]
                items_out.append(item)
            for key in oh["items"]:
                if key not in seen_item_keys:
                    self.err(f"kid_text.json: {name} item {key!r} not in her current_state inventory (stale?)")

            banner_ref = None
            if oh["banner"]:
                banner_ref = add_art(oh["banner"], f"{name} banner")
            self.lint_kid(oh["tagline"], f"{name} tagline")

            heroes_out.append(
                {
                    "id": oh["id"],
                    "name": name,
                    "class": ch["class"],
                    "joined": ch["joined"],
                    "accent": oh["accent"],
                    "banner": banner_ref,
                    "tagline": oh["tagline"],
                    "stats": ch["stats"],
                    "abilities": abilities_out,
                    "spells": spells_out,
                    "items": items_out,
                }
            )

        # --- party shared items ---
        shared_out = []
        shared_row = next((v for k, v in inventory.items() if k.startswith("Party")), None)
        if shared_row is None:
            self.err("current_state.md: no 'Party (shared)' row in the inventory table")
            shared_row = []
        shared_overlay = overlay["party"]["sharedItems"]
        seen_shared = []
        for raw in shared_row:
            clean = self.strip_md(raw)
            key = self.strip_trailing_paren(clean)
            seen_shared.append(key)
            ov = shared_overlay.get(key)
            if ov is None:
                self.err(
                    f"Shared item {clean!r} (key {key!r}) has no kid_text.json entry. "
                    f"Author it or it cannot ship."
                )
                continue
            self.lint_kid(ov["text"], f"shared item {key!r}")
            shared_out.append({"icon": ov["icon"], "name": ov.get("name", key), "text": ov["text"]})
        for key in shared_overlay:
            if key not in seen_shared:
                self.err(f"kid_text.json shared item {key!r} not in current_state inventory (stale?)")

        # --- quests: every canon quest needs an entry or an explicit hidden marker ---
        quests_out = []
        quest_overlay = overlay["quests"]
        canon_quest_names = [q[0] for q in canon_quests]
        for qname, raw_line in canon_quests:
            ov = quest_overlay.get(qname)
            if ov is None:
                self.err(
                    f"Canon quest {qname!r} has no allow-list decision. Add kid text or "
                    f'mark it {{"hidden": true, "reason": ...}} in tools/kid_text.json.'
                )
                continue
            if ov.get("hidden"):
                self.excluded.append(f"quest {qname!r}: {ov.get('reason', 'no reason given')}")
                continue
            self.lint_kid(ov["text"], f"quest {qname!r} text")
            self.lint_kid(ov["name"], f"quest {qname!r} name")
            quests_out.append({"icon": ov["icon"], "name": ov["name"], "text": ov["text"]})
        for qname in quest_overlay:
            if qname not in canon_quest_names:
                self.err(f"kid_text.json quest {qname!r} not found in current_state (stale?)")

        # --- journal: exactly one authored entry per canon session log ---
        journal_out = []
        for n in sorted(logs):
            if n not in journal:
                self.err(
                    f"Session {n} ({logs[n]!r}) has no entry in tools/journal.md. "
                    f"Author 2-4 short kid-readable sentences for it."
                )
                continue
            e = journal[n]
            self.lint_kid(e["text"], f"journal session {n} text")
            self.lint_kid(e["title"], f"journal session {n} title")
            journal_out.append({"session": n, "title": e["title"], "text": e["text"]})
        for n in journal:
            if n not in logs:
                self.err(f"journal.md has an entry for session {n} but canon has no such session log")

        # --- assemble ---
        if gold is None:
            gold_note = overlay["party"]["goldUnknownNote"]
            self.lint_kid(gold_note, "goldUnknownNote")
        else:
            gold_note = None

        last = max(journal_out, key=lambda e: e["session"]) if journal_out else None
        as_of = f"After Session {last['session']}: {last['title']}" if last else None

        pets = overlay["pets"]
        self.lint_kid(pets["text"], "pets text")

        if self.errors:
            return None, art_jobs

        data = {
            "schemaVersion": 1,
            "note": GENERATED_NOTE,
            "asOf": as_of,
            "party": {
                "name": overlay["party"]["name"],
                "gold": gold,
                "goldNote": gold_note,
                "sharedItems": shared_out,
            },
            "heroes": heroes_out,
            "pets": pets,
            "quests": quests_out,
            "journal": journal_out,
        }
        return data, art_jobs

    # ---------- art sync ----------

    def sync_art(self, art_jobs: dict[str, Path], check_only: bool, prune: bool) -> list[str]:
        actions = []
        ART_DIR.mkdir(parents=True, exist_ok=True)
        for dest_name, src in sorted(art_jobs.items()):
            dest = ART_DIR / dest_name
            if dest.is_file() and filecmp.cmp(src, dest, shallow=False):
                actions.append(f"  = {dest_name} (up to date)")
            elif check_only:
                actions.append(f"  ! {dest_name} would be {'updated' if dest.is_file() else 'copied'} from {src}")
            else:
                shutil.copy2(src, dest)
                actions.append(f"  + {dest_name} copied from {src}")
        orphans = [p for p in sorted(ART_DIR.iterdir()) if p.is_file() and p.name not in art_jobs]
        for p in orphans:
            if prune and not check_only:
                p.unlink()
                actions.append(f"  - {p.name} pruned (no longer needed)")
            else:
                self.err(
                    f"app/art/{p.name} is not needed by the current export. Shipped art "
                    f"must be allow-listed. Re-run with --prune-art to delete it, or add "
                    f"whatever needs it."
                )
        return actions


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--canon-root", type=Path, default=DEFAULT_CANON_ROOT)
    ap.add_argument("--check", action="store_true", help="validate and report, write nothing")
    ap.add_argument("--prune-art", action="store_true", help="delete no-longer-needed files in app/art/")
    args = ap.parse_args()

    if not args.canon_root.is_dir():
        print(f"EXPORT FAILED: canon root not found: {args.canon_root}", file=sys.stderr)
        return 2

    overlay = json.loads(KID_TEXT_PATH.read_text(encoding="utf-8"))
    ex = Exporter(args.canon_root)
    data, art_jobs = ex.build(overlay)

    art_actions = ex.sync_art(art_jobs, check_only=args.check or bool(ex.errors), prune=args.prune_art)

    for w in ex.warnings:
        print(f"WARNING: {w}")

    if ex.errors:
        print(f"\nEXPORT FAILED with {len(ex.errors)} error(s). Nothing was written.", file=sys.stderr)
        for i, e in enumerate(ex.errors, 1):
            print(f"  {i}. {e}", file=sys.stderr)
        return 2

    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    existing = OUT_PATH.read_text(encoding="utf-8") if OUT_PATH.is_file() else None
    changed = payload != existing

    print("Secrets filter exclusions (GM eyes only):")
    for x in ex.excluded or ["  (none)"]:
        print(f"  {x}" if not x.startswith("  ") else x)
    print("Art:")
    for a in art_actions:
        print(a)

    if args.check:
        print(f"\nCHECK OK. {OUT_PATH.name} would {'change' if changed else 'be unchanged'}.")
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(payload, encoding="utf-8", newline="\n")
    print(f"\nWrote {OUT_PATH} ({'changed' if changed else 'no content change'}).")
    print(f"Heroes: {len(data['heroes'])}. Quests shown: {len(data['quests'])}. "
          f"Journal entries: {len(data['journal'])}. As of: {data['asOf']}")
    if changed:
        print("Reminder: bump CACHE_VERSION in app/sw.js before deploying.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
