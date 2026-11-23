# Art: living page

The page is `art-bible` (area Art), and no other page. It grows per topic; keep it under the wiki's split rule.

```markdown
## Slogan
<one line>

## Rule-pillars
1. <rule>: rules out <x>; serves <pillar>. Fails if <a check on a capture>.

## Colour roles
| Role | Hex | Used for | Never used for |
|---|---|---|---|
(reserved hues for self, threat, interactable, pickup; the environment keeps out of them)

## Value bands per layer
| Layer (UI, characters, VFX, environment) | Value range | Saturation range |
|---|---|---|

## Silhouette rules
<each class of thing, how it must read at thumbnail size and in grayscale>

## UI visual language
<palette by function, type scale and minimum size, icon grammar>

## Motion and VFX rules
<timing, primary and secondary element, clutter budget, value limits>

## Invariants it protects
<the art-related lines of the identity invariants, as written in vision.json>
```

The hex table is the check: `measure.py palette` reads it. Every row has a hex and a role.
