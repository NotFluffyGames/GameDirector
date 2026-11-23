---
name: game-research
description: Research the game's market and references. Before ideation, alone, a landscape scan of comparable games, the genre's anchors and defaults, player complaints and candidate references; after ideation, one session per reference opened for study, writing per-role dossiers, then a brief and the person's homework, which brainstorm waits on. Handles the scan and research phases of the game-* workflow; also re-scans after a restart.
disable-model-invocation: true
---

# Game Research

Keeps the game from being designed from memory. The **scan** maps the landscape before ideation, so the person chooses a direction that isn't generic; the **deep study** reads the references ideation opened, one per session, so brainstorm grills topics with evidence. What the agent can't do itself becomes the person's homework in `docs/game/research/homework.json`, and brainstorm waits for it. Read `docs/agents/game.md` first and follow its session rules.

## Modes

| Task | Mode |
| --- | --- |
| `game-research scan` | phase scan, alone: the `landscape` page and the candidate references in `references.json` |
| `game-research ref <id>` | phase research, alone: study one open reference into a dossier per role, then audit it |
| `game-research brief` | phase research, alone: the `research` page from the dossiers, and `homework.json` |
| `game-research homework` | with a person, before brainstorm: answer or skip each open homework item |
| `game-research restart <adr>` | phase scan after a restart: re-scan in light of the ADR, keeping studied dossiers |
