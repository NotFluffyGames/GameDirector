# Topic map

The first-level topics ideation seeds under `T1`. Seed one per row this game needs, worded for this game (not the generic question below), with the id of the page it will write (the page is created when the topic is brainstormed, in the wiki area that fits it). Skip rows the vision rules out, and add rows for anything the vision raises that the map lacks. Mark each topic's `stage`: `slice` when the `slice` page's In list needs it answered, otherwise `production`; a topic the slice needs only part of becomes two topics, one per stage.

Every topic gets `roles`: start from the Roles column (the area table in `docs/agents/game.md`), add `creative` to every `core` topic, add or drop a role by judgment, and leave out each role in `vision.json` `roles_off`.

| Area | Typical question | Priority | Page id | Roles |
| --- | --- | --- | --- | --- |
| Core loop | What exactly happens, step by step, in one cycle of the core loop, and what decision does the player make each time? | core | `mechanics` | design, feel, creative |
| Rules | What are the objects, actions, win and fail conditions, and how are ties, timeouts and simultaneous actions resolved? | core | `mechanics` | design, feel, creative |
| Controls | Which input actions exist, how are they bound per device, and how do they feel? | core | `controls` | feel, ux, creative |
| Each system the vision names | What does this system do, what are its knobs, and which other systems does it change? | support | `<system>` | design |
| Progression | What does the player gain across a session and across sessions? | support | `progression` | design |
| Difficulty and AI | How is challenge set and adapted; what do opponents or enemies do? | support | `ai` | design |
| Each content type | What kit pieces build it, how many pieces, and what makes two pieces play differently? | support | `<content-type>` | design, and the roles its pieces touch: art, audio, narrative |
| Modes and sessions | Which modes exist, how does a session start, flow and end, and how do sessions connect? | support | `modes` | design, ux |
| Multiplayer and netcode | Local or networked; if networked, which model? | core when networked | `netcode` | design, creative |

## The roles' pages

Each active role except `creative` and `design` gets one **slice** topic for its page, with that role in `roles`; `gamestate.py gate` names each one missing. The page is laid out by the role skill's `page-template.md` and filled to the slice's quality bar.

| Role | Typical question | Priority | Page id | Roles |
| --- | --- | --- | --- | --- |
| `feel` | What does each core action's feel sheet say: intent, response frames, buffer and forgiveness windows, feedback layers, camera? | support | `feel` | feel, audio, art |
| `art` | What does the art bible say for the slice: colour roles as hex values, value bands, silhouettes, UI visual language, motion and VFX, precisely enough to check a capture against? | support | `art-bible` | art |
| `audio` | What does the audio page say for the slice: what the player does by ear, the palette per category, signature sounds, priority tiers, the music scheme, the UI sound family, the loudness target? | support | `audio` | audio |
| `narrative` | What do the fantasy, setting, tone, UI voice, naming rules and glossary say, as deep as the slice's play needs (at least the minimum kit)? | support | `tone-and-world` | narrative |
| `ux` | What is the screen flow from launch to quit, what does the HUD carry and through which channel, and how does a new player learn the core verb in the first minute? | support | `screens`, `onboarding` | ux, art |

`creative`'s page is the `vision` page, which ideation writes; `design`'s pages come from the core loop, rules, systems and content rows. A role's production-stage depth (more content, more screens, the full mix) becomes its own `production` topic.

Brainstorm then works each topic through with the user and breaks it down further, one topic per conversation.
