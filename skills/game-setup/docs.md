# Docs next to the tasks

Where the wiki and the GDD live, so they sit next to the tasks. The game-* skills write the wiki pages and the GDD here and read people's comments back from them. Setup fills this file with the user and records the smoke test below.

## Tasks home

<Where the tasks live, matching `issue-tracker.md`: tracker, space or project, list.>

## Docs place

<Which tool holds the docs, and where in it. Default: the docs feature of the tracker above (a docs page beside the task list, the tracker's wiki), or the docs tool the team uses beside it. Local files (`docs/game/wiki/` for the wiki, `docs/gdd/` for the GDD) only when the user chose them.>

## How to read, write and comment

<The tools or commands for each: create a page, read its current text and version, update a page, read comments and reply, link a page from a task, delete a page, protect the wiki. People comment and sessions edit.>

<A page's **version**, as `wiki.json` records it: the docs tool's version number for the page; where it has none, its last-modified time; where it has neither, a hash of the page's text as read back (`git hash-object --stdin`). Write here which one this place uses.>

<Local files: sessions edit the markdown files. People comment in a `## Comments` section at the end of each page (or in review comments on the commits that change it), and sessions reply there. A page's version is the git hash of its text above that section: `sed '/^## Comments/,$d' <file> | git hash-object --stdin`, so a comment is not an edit. A task links a page by its repo path. Local files can't be protected: tell the user, and record that in the protect row.>

## Smoke test

Run in the docs place during setup, on a test page; every step must pass before setup completes. The one exception is `protect the wiki`: where the tool has no page permissions, it reads `not supported (user told)` once you have told the user.

| Step | Result | Date |
| --- | --- | --- |
| create | | |
| read | | |
| read version or last-modified | | |
| edit (and the version moves) | | |
| comment | | |
| read comments | | |
| link from a task | | |
| delete | | |
| protect the wiki | | |

## Wiki pages

| Page id | Link |
| --- | --- |
| index | |

The ids match `docs/game/wiki.json`, which holds every page; list here the pages that anchor the wiki. Setup records the home page, `index`.

## GDD pages

| GDD page | Link |
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

Setup creates these pages, each holding only its title, and records their links; game-gdd fills them and records any page it adds.
