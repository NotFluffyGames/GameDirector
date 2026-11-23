---
name: game-gdd
description: Sync the human-facing game design document, kept next to the tasks, from the agent-facing wiki, both in the docs place - create it the first time, rewrite the sections whose wiki pages changed, show the AI's own calls, and turn people's comments and direct edits into brainstorm topics or kept values. Runs whenever the wiki changed before a phase or milestone moves on.
disable-model-invocation: true
---

# Game GDD

The **GDD** is for people: a readable design document that lives next to the tasks, where `docs/agents/docs.md` says. The **wiki** is for agents and is the source of truth; its pages are in the same docs place, indexed in `docs/game/wiki.json` ("The wiki" in `docs/agents/game.md`). This step makes the GDD say what the wiki says, in plain language, and carries people's reactions back as topics. Read `docs/agents/game.md` first and follow its session rules.

## 1. Find what changed

Read `docs/agents/docs.md` for where the GDD lives, how to read and write it, and its page list. Then list the wiki pages changed since the last sync, from the files in the repo:

```bash
git diff <state.json gdd_synced> HEAD -- docs/game/wiki.json docs/game/vision.json docs/game/own-calls.md
```

The `version` and `updated` fields of each page entry show which pages changed. With no `gdd_synced` yet, every page is new: the GDD gets created.

Then detect direct edits: read each page's current version in the docs tool and compare it with the `version` in `wiki.json`. A mismatch is an edit nobody committed through a session (including a page whose session died before recording it). A page missing from the docs tool counts as edited. Each mismatch becomes an open topic quoting what changed (a diff or the changed passage), with the page in its `pages`, mirrored as a `ready-for-human` ticket; give the page a `flagged` entry (`{"topic": "T031", "note": "..."}`) in `wiki.json` and put a visible note on the page pointing at the topic. The topic's brainstorm decides what the page says; until then the GDD shows the committed text, and the flagged page's GDD section says it is under review.

**Done when** you have the list of changed wiki pages, every version mismatch or missing page is a topic with a `flagged` entry and a note, and you know the GDD sections each changed page feeds ([gdd-structure.md](gdd-structure.md)).

## 2. Bring people's input back

Before writing over anything, read the GDD sections you are about to update, and the comments on them and on the wiki pages, for changes people made since the last sync. Each edit or comment that asks for a different design becomes an open topic (priority by its weight, its question in the person's words, the commenter named), mirrored as a `ready-for-human` ticket. Reply on the comment with the topic's ticket. A comment that says to keep something a tuning value controls becomes a `docs/game/keep.json` entry with the comment as its source, and a pin per knob. A comment on an own call either keeps it (no change) or opens a topic to change it. Corrections of wording only can be applied to the wiki page, written last as step 4 says.

**Done when** every human edit and comment since the last sync, on the GDD or the wiki, is a topic, a wiki fix or an answered reply.

## 3. Write the GDD

Create or update each affected section per [gdd-structure.md](gdd-structure.md): plain language, short paragraphs, tables and lists where they read better, one link per section back to its wiki pages and topics. Keep the **Status** page current from `gamestate.py status`: stage and phase, what is built and verified, the last verdict's scores, open topics. List the own calls added since the last sync on the **Own calls** page, newest first, each inviting a keep-or-change comment.

**Done when** every changed wiki page's content reads correctly in its GDD section, and the Status section matches status.

## 4. Close

Record any new page ids or links in `docs/agents/docs.md`, commit the state (`wiki.json` flags, topics), run `python3 docs/game/gamestate.py gdd-synced`, append a progress entry. Then write the wording fixes to wiki pages from step 2, last, record their new `version` and `updated` in `wiki.json`, and commit that.

**Done when** `gdd-synced` succeeds and every wiki page written here has its `wiki.json` entry committed.
