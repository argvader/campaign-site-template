# campaign-site-template

A "create-react-app"-style generator for tabletop RPG **campaign archive sites**.
Answer a few questions and it stamps out a ready-to-run repo: an MkDocs Material
site, the session→wiki content pipeline, Claude Code skills, the two master prompts
(`SESSION_SUMMARIZER.md`, `WORLD_PAGE.md`), helper scripts, and a starter world
bible — all themed to your campaign.

It's the reusable, campaign-agnostic distillation of a working setup: raw session
audio → Deepgram transcript → Claude Code skills that write Markdown wiki/session
pages + AI art → `git push` → GitHub Pages.

## What you get

A generated repo with:

- `docs/` — the MkDocs site (themed `stylesheets/extra.css`, a starter home page,
  empty `wiki/{pcs,npcs,factions,locations}` and `sessions/` ready to fill).
- `mkdocs.yml`, `requirements.txt`, `.github/workflows/deploy-docs.yml` — build +
  GitHub Pages deploy.
- `.claude/skills/{summarize-session,build-world,publish-site}` — drive the pipeline
  by name in Claude Code.
- `SESSION_SUMMARIZER.md`, `WORLD_PAGE.md` — the master prompts (with your roster and
  setting baked in).
- `bin/` (image generation + maintenance scripts), `hooks/wiki_images.py`,
  `world/world.md` skeleton, `README.md`, `.env.example`.

## Usage

### Option A — clone and run in place (like `create-react-app`)

```bash
git clone <this-repo-url> my-campaign
cd my-campaign
python init.py           # answer the questions
rm -rf .git && git init  # fresh history; then add your GitHub remote
```

`init.py` renders the template in place, then deletes itself, `GENERATOR.md`,
`answers.example.json`, and the `template/` folder — leaving a clean campaign repo.

### Option B — generate into an existing (empty) repo

```bash
python init.py /path/to/my-campaign            # interactive
python init.py /path/to/my-campaign --answers answers.json   # non-interactive
```

Renders into `TARGET_DIR` and leaves this template clone untouched — handy when the
target repo already exists (e.g. you created it on GitHub and cloned an empty repo).

### The interview

`init.py` asks for: campaign name, GitHub user + repo slug (→ Pages URL), tagline,
game system, genre/tone, three theme colors (accent, secondary accent, dark
background), three fonts (heading/body/mono), an art-style suffix, the DM's name, and
the player roster. Every question has a default; press Enter to accept it. Pass
`--answers answers.json` to skip the interview — see `answers.example.json`.

Colors drive `docs/stylesheets/extra.css` (shades are derived with CSS `color-mix`),
the fonts drive the headings/body, and the art-style suffix is appended to every
image prompt by `bin/gen-image.py`. The roster populates the Participants table and
the Deepgram speaker-mapping in `SESSION_SUMMARIZER.md` + `README.md`.

## After generating

1. `cp .env.example .env` and add `DEEPGRAM_API_KEY` + `OPENAI_API_KEY`.
2. `pip install -r requirements.txt && mkdocs build --strict` (should pass clean).
3. `mkdocs serve` to preview.
4. Fill in `world/world.md`, record your first session, and follow the generated
   `README.md`.
