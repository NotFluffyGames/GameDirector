# Audio: living page

The page is `audio` (area Audio), and no other page. It grows per topic; keep it under the wiki's split rule.

```markdown
## Pillars
1. <one or two sentences>: this, not that. Serves <game pillar>.

## Reference vocabulary
<five to fifteen references, each with the one quality borrowed, and the anti-references>

## What the player does by ear
<the information that is audio-first, and what the player must be able to do with it>

## Palette per category
| Category (player, threats, world, UI, music, voice) | Sources | Timbre and frequency zone | Processing chain | Never |
|---|---|---|---|---|

## Signature sounds
<three to seven sounds that define the game: the event, how it is made, the cue that must survive variation>

## Priority tiers
| Tier | Events | Ducks | Voice limit |
|---|---|---|---|
(player-critical information; own-action feedback; others' actions; ambience and music)

## Variation minimums
<per event class: minimum variations, longest allowed back-to-back repeat>

## Music scheme
<role, instrumentation, states and their transitions, silence policy>

## UI sound family
<shared key, timbre and envelope for confirm, cancel, navigate, error, reward>

## Loudness target
<integrated target and tolerance, true-peak ceiling, per platform; "not measured" where the adapter can't>

## Accessibility
<per-category volume sliders, mono option, captions, a visual cue for every critical sound>

## Invariants it protects
<the audio-related lines of the identity invariants, as written in vision.json>
```

Every gameplay event has a row in the event list the page points to. The variation and repeat rules are numbers a log can check.
