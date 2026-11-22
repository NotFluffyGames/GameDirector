# Issue tracker: Local Markdown

Tickets for this repo live as markdown files in `.scratch/`.

## Conventions

- One effort per directory: `.scratch/<slug>/` (the game's tickets: `.scratch/game/`)
- One file per ticket: `.scratch/<slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order
- Near the top of each file: `Status:` (a triage label from `triage-labels.md`, or `claimed` / `done`), `Blocked by:` (ticket numbers, or `None`), `Features:` (feature ids from `docs/game/features.json`)
- Comments and history append under a `## Comments` heading at the bottom

## When a skill says "publish to the issue tracker"

Create the file under `.scratch/<slug>/issues/`, creating directories as needed.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path or number.

## Frontier

Open tickets whose `Blocked by` tickets are all `done`, with status `ready-for-agent`; lowest number first. Claim by setting `Status: claimed` before work; close by setting `Status: done`.
