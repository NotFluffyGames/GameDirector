# GDD structure

The human-facing GDD, as one document with these pages (or sections, where the docs tool has no pages). The GDD and the wiki are in the same docs place. Each GDD page is written from the wiki pages (ids in `docs/game/wiki.json`) listed beside it; one wiki page can feed several GDD pages.

| GDD page | From the wiki | Written for |
| --- | --- | --- |
| **Overview** | the `vision` and `concepts` pages | anyone: what the game is, who it is for, why it will be fun, the pillars and anti-pillars, the kill condition, what was considered and why this |
| **Direction** | `vision.json` `north_stars` and `invariants`, the `vision` page's direction per role and its references | each role's north star in a line or two (what it aims at, what we take from each reference, what it must never become), and the identity invariants polish must keep |
| **Landscape and research** | the `landscape` and `research` pages, `docs/game/research/homework.json` and its homework page | the comparable games and the genre default the game departs from, what the studied references teach, what is still unknown, and the homework open for people, linked rather than copied |
| **Vertical slice** | the `slice` page | what is built first, what it must prove, its quality bar, and how it will be playtested |
| **Gameplay** | Mechanics and Controls pages | how a match or run plays, step by step, with the controls |
| **Systems** | Systems pages | each system in a paragraph, and a short table of how systems affect each other |
| **Content** | Content pages | what content there is, how much, and what makes pieces differ |
| **Modes and sessions** | Modes pages | the modes and how a session flows |
| **Screens and onboarding** | Screens pages | the screen flow, and a new player's first minute |
| **Look, sound and feel** | Feel, Art, Audio, and Narrative and world pages | the art bible, the sound and the tone and world in brief, and how core actions should feel |
| **The bar** | `fun-checklist.json`, `richness.json` | what "fun" and "rich" mean for this game, and how they are measured |
| **Status** | `gamestate.py status`, the latest verdict ADR, the review files and their decisions | where the game stands: stage and phase, what is built and verified, last verdict scores, open topics and how to join them, and the roles' review decisions since the last sync |
| **Own calls** | `own-calls.md` | the player-visible choices agents made that no page specified, newest first, for people to keep or change |
| **Kept** | `keep.json` | what playtests, comments and A/B picks said to keep, and the values pinned for it |
| **Changes** | page `Last changed` lines, ADRs | a dated log of design changes and why, newest first |

Rules:

- Plain language. Explain a game term the first time each page uses it; keep the agent-facing precision (exact numbers, edge cases) in the wiki and link to it.
- Each page ends with "Source: wiki pages …, topics …", with a link to each page, so a reader can follow a section back to where it was decided.
- Never edit the wiki to match the GDD; the GDD follows the wiki. People's edits, on either, come back as topics, and an edited wiki page is flagged in `wiki.json` until its topic resolves.
