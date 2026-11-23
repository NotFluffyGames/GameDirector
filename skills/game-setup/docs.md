# Docs next to the tasks

Where the wiki and the GDD live, so they sit next to the tasks. The game-* skills write the wiki pages and the GDD here and read people's comments back from them. Setup fills this file with the user and records the smoke test below.

## Tasks home

<Where the tasks live, matching `issue-tracker.md`: tracker, space or project, list.>

## Docs place

<Which tool holds the docs, and where in it. Default: the docs feature of the tracker above (a docs page beside the task list, the tracker's wiki), or the docs tool the team uses beside it. Local files (`docs/game/wiki/` for the wiki, `docs/gdd/` for the GDD) only when the user chose them.>

## How to read, write and comment

<The tools or commands for each: create a page, read its current text and version, update a page, read comments and reply, link a page from a task, delete a page, protect a page. People comment and sessions edit.>

## Smoke test

Run in the docs place during setup; every step must pass before setup completes.

| Step | Result | Date |
| --- | --- | --- |
| create | | |
| read | | |
| edit | | |
| comment | | |
| read comments | | |
| link from a task | | |
| delete | | |
| protect pages | | |

## Wiki pages

| Id | Id or link |
| --- | --- |
| vision | |
| slice | |
| concepts | |

The ids match `docs/game/wiki.json`, which holds every page; list here the pages that anchor the wiki, such as its home page.

## GDD pages

| GDD page | Id or link |
| --- | --- |
| Overview | |
| Vertical slice | |
| Gameplay | |
| Systems | |
| Content | |
| Modes and sessions | |
| Screens and onboarding | |
| Look, sound and feel | |
| The bar | |
| Status | |
| Own calls | |
| Kept | |
| Changes | |

game-gdd fills in the ids and links when it creates the pages.
