# TShirt-AI - Ralphthon Hackathon Project

AI system that detects events, extracts themes, generates inside-joke slogans, and creates t-shirt designs using Gemini image generation. Built autonomously by Ralph + Claude Code.

## Setup

```bash
# 1. Create .env with your API keys
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY and WANDB_API_KEY

# 2. Install jq (needed by Ralph)
brew install jq
```

## Run Ralph (autonomous build)

```bash
./scripts/ralph/ralph.sh 10
```

Ralph will:
1. Pick the next task from `prd.json`
2. Implement it using Claude Code
3. Run checks
4. Commit changes
5. Move to next task
6. Repeat until all 8 tasks are done

## Run the app (after Ralph builds it)

```bash
source venv/bin/activate
python run.py
```

## Check progress

```bash
# See which tasks are done
cat prd.json | jq '.userStories[] | {id, title, passes}'

# See Ralph's learnings
cat progress.txt

# See git history
git log --oneline
```

## Project structure

```
Ralphthon/
├── scripts/ralph/ralph.sh   # Autonomous loop
├── CLAUDE.md                 # Agent instructions per iteration
├── prd.json                  # Task list (Ralph updates this)
├── progress.txt              # Ralph's learnings
├── data/events.json          # Mock event data (input)
├── app/                      # Source code (Ralph builds this)
├── output/                   # Generated designs
├── .env                      # API keys (not committed)
├── requirements.txt          # Python dependencies
└── docs/w&b.md               # W&B Weave research
```

## Extending

Add new tasks to `prd.json` following the existing format. Each story needs:
- `id`, `title`, `description`
- `acceptanceCriteria` (list of testable checks)
- `priority` (order of execution)
- `passes: false`
