# UX: living pages

Two pages, area Screens and onboarding, and no others: `screens` and `onboarding`. They grow per topic; keep each under the wiki's split rule.

## `screens`

```markdown
## Target player
<one to three short profiles: genre experience, session context, platform and input device, access needs>

## Flow map
<boot, title, menus, play, pause, fail and retry, results; the back path at each; clicks from launch to first play>

## HUD information hierarchy
| Information | Priority (critical, situational, nice-to-know) | Channel (world, HUD, audio, haptic) | Zone | Behaviour |
|---|---|---|---|---|

## Input map
<verb to input per device; hold or tap; conflicts; remapping>

## Text and contrast
<minimum text size by screen; the contrast ratios for text and large text; the regions a capture measures>

## Accessibility minimum
<remapping, separate volume sliders, subtitles on or offered at first launch, text size, colour-safe palette with redundant cues, shake and flash toggles, assist options, hold-to-toggle alternatives; each as present or planned>

## Invariants it protects
<the ux-related lines of the identity invariants, as written in vision.json>
```

## `onboarding`

```markdown
## First-minute plan
<ordered: what must be learned to reach the core loop; for each, where and how it is taught, how doing confirms it, what failure looks like>

## Time targets
Launch to control <s>; to first core action <s>; to first payoff <s>.

## Deferred
<what is deliberately taught later>

## Events per step
<an event-log name per step, so a log can time it>

## Skip and replay
<how the player skips or replays it>
```

Each target is a number a log or a capture can check; every flow step has a capture state that shows it.
