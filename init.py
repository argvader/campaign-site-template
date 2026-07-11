#!/usr/bin/env python3
"""Scaffold a new tabletop-campaign site from this template.

Like create-react-app: it asks a handful of questions, then stamps out a ready-to-run
MkDocs Material campaign repo — the session/wiki pipeline, Claude Code skills, the two
master prompts, a themed site skeleton, and a starter world bible.

Usage:
    python init.py [TARGET_DIR] [--answers answers.json] [--force]

    (no TARGET_DIR)   Render the template in place — for the
                      `git clone <template> my-campaign && cd my-campaign` flow.
                      Afterwards this script, GENERATOR.md, answers.example.json and
                      the template/ folder are removed, leaving a clean campaign repo.

    TARGET_DIR        Render into that directory instead (e.g. an already-created,
                      empty repo). The template clone is left untouched.

    --answers FILE    Read answers from a JSON file instead of prompting. Every key is
                      optional; missing keys fall back to the same defaults the
                      interview offers. See answers.example.json.

    --force           Overwrite existing files in TARGET_DIR without asking.

Standard library only — no pip install.
"""

import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(HERE, "template")

# Generator-only files removed after an in-place render (they don't belong in a
# generated campaign repo).
GENERATOR_ONLY = ("init.py", "GENERATOR.md", "answers.example.json")

# (key, prompt, default) for the interview. Colors are hex; fonts are Google Fonts
# family names. art_style_suffix is appended to every image prompt by bin/gen-image.py.
QUESTIONS = [
    ("campaign_name", "Campaign name", "My Campaign"),
    ("github_user", "GitHub username (for the Pages URL)", "your-user"),
    ("repo_slug", "Repo name (GitHub repo / URL slug)", None),  # default derived below
    ("tagline", "One-line tagline for the home page", "A tabletop campaign chronicle."),
    ("game_system", "Game system", "Dungeons & Dragons 5th Edition"),
    ("genre_tone", "Genre / tone (a few words)", "high fantasy"),
    ("accent_color", "Accent color (hex)", "#c8a54e"),
    ("secondary_accent", "Secondary accent color (hex)", "#c9622f"),
    ("dark_bg", "Dark background base color (hex)", "#17130d"),
    ("heading_font", "Heading font (Google Fonts name)", "Cinzel"),
    ("body_font", "Body font (Google Fonts name)", "Marcellus"),
    ("mono_font", "Monospace font (Google Fonts name)", "Fira Mono"),
    (
        "art_style_suffix",
        "Art style suffix (appended to every image prompt)",
        "cinematic fantasy illustration, painterly, dramatic light, no text or lettering.",
    ),
    ("dm_name", "Dungeon Master's name", "DM"),
]


def _slugify(name):
    """Campaign name -> repo slug: lowercase, non-alphanumeric runs -> single '_'."""
    out = []
    prev_us = False
    for ch in name.strip().lower():
        if ch.isalnum():
            out.append(ch)
            prev_us = False
        elif not prev_us:
            out.append("_")
            prev_us = True
    return "".join(out).strip("_") or "campaign"


def _ask(prompt, default):
    suffix = f" [{default}]" if default else ""
    try:
        reply = input(f"  {prompt}{suffix}: ").strip()
    except EOFError:
        reply = ""
    return reply or default


def _ask_roster():
    """Interactively collect the player roster (may be empty)."""
    roster = []
    print("\n  Player roster (press Enter at 'Player name' to finish; leave empty to skip):")
    while True:
        player = input("    Player name: ").strip()
        if not player:
            break
        character = input("    Character name: ").strip()
        ancestry = input("    Ancestry/species: ").strip()
        char_class = input("    Class/role: ").strip()
        roster.append(
            {
                "player": player,
                "character": character,
                "ancestry": ancestry,
                "class": char_class,
            }
        )
    return roster


def collect_answers(answers_path):
    """Return the answers dict, from a JSON file or by interview."""
    if answers_path:
        with open(answers_path, encoding="utf-8") as fh:
            data = json.load(fh)
        answers = {}
        for key, _prompt, default in QUESTIONS:
            answers[key] = str(data.get(key, default if default is not None else ""))
        if not answers.get("repo_slug"):
            answers["repo_slug"] = _slugify(answers["campaign_name"])
        answers["roster"] = data.get("roster", []) or []
        return answers

    print("\nNew campaign site — answer a few questions (Enter accepts the default).\n")
    answers = {}
    for key, prompt, default in QUESTIONS:
        if key == "repo_slug":
            default = _slugify(answers.get("campaign_name", "campaign"))
        answers[key] = _ask(prompt, default)
    answers["roster"] = _ask_roster()
    return answers


def _roster_table(roster):
    """The Participants table for SESSION_SUMMARIZER.md."""
    if not roster:
        return (
            "_No player roster recorded yet — add players and their characters here "
            "after your first session._"
        )
    lines = [
        "| Player | Character | Ancestry | Class |",
        "|--------|-----------|----------|-------|",
    ]
    for m in roster:
        lines.append(
            f"| {m.get('player','')} | {m.get('character','')} "
            f"| {m.get('ancestry','')} | {m.get('class','')} |"
        )
    return "\n".join(lines)


def _speaker_labels_table(roster, dm_name):
    """The Deepgram-speaker -> label table for README.md."""
    lines = [
        "| Deepgram speaker | Label to use |",
        "|------------------|--------------|",
        f"| (the DM's voice) | `{dm_name} the DM` |",
    ]
    for m in roster:
        player = m.get("player", "")
        character = m.get("character", "")
        lines.append(f"| {player} | `{player} as {character}` |")
    return "\n".join(lines)


def _speaker_map_json(roster, dm_name):
    """The jq --argjson speaker map for README.md (a JSON object literal)."""
    entries = [f'  "0":"{dm_name} the DM"']
    for i, m in enumerate(roster, start=1):
        entries.append(f'  "{i}":"{m.get("player","")} as {m.get("character","")}"')
    return "{\n" + ",\n".join(entries) + "\n}"


def build_context(answers):
    """Expand answers into the full {{token}} -> value map used for substitution."""
    ctx = {k: v for k, v in answers.items() if k != "roster"}
    roster = answers.get("roster", [])
    dm_name = answers.get("dm_name", "DM")
    ctx["site_url"] = f"https://{answers['github_user']}.github.io/{answers['repo_slug']}/"
    ctx["heading_font_url"] = answers["heading_font"].replace(" ", "+")
    ctx["roster_table"] = _roster_table(roster)
    ctx["speaker_labels_table"] = _speaker_labels_table(roster, dm_name)
    ctx["speaker_map_json"] = _speaker_map_json(roster, dm_name)
    return ctx


def _substitute(text, ctx):
    for key, value in ctx.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def render(ctx, out_dir, force):
    """Render every template file into out_dir with tokens substituted."""
    written = []
    conflicts = []
    for root, _dirs, files in os.walk(TEMPLATE_DIR):
        for name in files:
            src = os.path.join(root, name)
            rel = os.path.relpath(src, TEMPLATE_DIR)
            dst = os.path.join(out_dir, rel)

            if os.path.exists(dst) and not force and os.path.abspath(dst) != os.path.abspath(src):
                conflicts.append(rel)
                continue

            os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
            with open(src, "rb") as fh:
                raw = fh.read()
            try:
                out = _substitute(raw.decode("utf-8"), ctx).encode("utf-8")
            except UnicodeDecodeError:
                out = raw  # binary asset — copy verbatim
            with open(dst, "wb") as fh:
                fh.write(out)
            shutil.copymode(src, dst)
            written.append(rel)

    return written, conflicts


def cleanup_in_place():
    """After an in-place render, drop generator-only files and the template/ dir."""
    for name in GENERATOR_ONLY:
        path = os.path.join(HERE, name)
        if os.path.exists(path):
            os.remove(path)
    if os.path.isdir(TEMPLATE_DIR):
        shutil.rmtree(TEMPLATE_DIR)


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new campaign site.")
    parser.add_argument("target_dir", nargs="?", help="Directory to generate into (default: in place).")
    parser.add_argument("--answers", help="JSON file with answers (skip the interview).")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files in TARGET_DIR.")
    args = parser.parse_args()

    if not os.path.isdir(TEMPLATE_DIR):
        print(f"init: template directory not found at {TEMPLATE_DIR}", file=sys.stderr)
        sys.exit(1)

    in_place = args.target_dir is None
    out_dir = HERE if in_place else os.path.abspath(args.target_dir)

    answers = collect_answers(args.answers)
    ctx = build_context(answers)

    print(f"\nGenerating '{answers['campaign_name']}' into {out_dir} ...")
    written, conflicts = render(ctx, out_dir, args.force)

    if conflicts:
        print(f"\ninit: {len(conflicts)} file(s) already exist and were skipped "
              f"(use --force to overwrite):", file=sys.stderr)
        for rel in conflicts:
            print(f"  - {rel}", file=sys.stderr)

    print(f"  wrote {len(written)} file(s).")

    if in_place:
        cleanup_in_place()
        print("  removed generator files (init.py, GENERATOR.md, answers.example.json, template/).")
        print("\nDone. This directory is now your campaign repo.")
        print("Next: for a fresh history run  rm -rf .git && git init  and set your remote,")
    else:
        print(f"\nDone. Scaffolded into {out_dir} (template clone left untouched).")
        print("Next:")

    print(f"  1. cp .env.example .env   # add DEEPGRAM_API_KEY + OPENAI_API_KEY")
    print(f"  2. pip install -r requirements.txt && mkdocs build --strict")
    print(f"  3. mkdocs serve           # preview at http://127.0.0.1:8000")
    print(f"  4. Fill in world/world.md, then record your first session (see README.md).")


if __name__ == "__main__":
    main()
