---
name: game-gdd
description: Sync the human-facing game design document, kept next to the tasks, from the agent-facing wiki - create it the first time, rewrite the sections whose wiki pages changed, and turn people's comments and edits into brainstorm topics. Runs whenever the wiki changed before a phase or milestone moves on.
disable-model-invocation: true
---

# Game GDD

The **GDD** is for people: a readable design document that lives next to the tasks, where `docs/agents/human-docs.md` says. The **wiki** (`docs/game/wiki/`) is for agents and is the source of truth. This step makes the GDD say what the wiki says, in plain language, and carries people's reactions back as topics. Read `docs/agents/game.md` first and follow its session rules.

## 1. Find what changed

Read `docs/agents/human-docs.md` for where the GDD lives, how to read and write it, and its page list. Then list the wiki pages changed since the last sync:

```bash
git diff --name-only <state.json gdd_synced> HEAD -- docs/game/wiki
```

With no `gdd_synced` yet, every page is new: the GDD gets created.

**Done when** you have the list of changed wiki pages and the GDD sections each one feeds ([gdd-structure.md](gdd-structure.md)).

## 2. Bring people's input back

Before writing over anything, read the GDD sections you are about to update, and their comments, for changes people made since the last sync. Each edit or comment that asks for a different design becomes an open topic (priority by its weight, its question in the person's words, the commenter named), mirrored as a `ready-for-human` ticket. Reply on the comment with the topic's ticket. Corrections of wording only can be applied to the wiki page directly.

**Done when** every human edit and comment since the last sync is a topic, a wiki fix or an answered reply.

## 3. Write the GDD

Create or update each affected section per [gdd-structure.md](gdd-structure.md): plain language, short paragraphs, tables and lists where they read better, one link per section back to its wiki pages and topics. Keep the **Status** section current from `gamestate.py status`: phase, what is built and verified, the last verdict's scores, open topics.

**Done when** every changed wiki page's content reads correctly in its GDD section, and the Status section matches status.

## 4. Close

Record any new page ids or links in `docs/agents/human-docs.md`, commit, run `python3 docs/game/gamestate.py gdd-synced`, append a progress entry.
