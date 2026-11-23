# Narrative: living page

The page is `tone-and-world` (area Narrative and world), and no other page. It grows per topic and only as deep as play needs; keep it under the wiki's split rule. A story-light game fills at least the minimum kit: fantasy line, setting, theme phrase, tone, character cards, UI voice, naming rules and the fiction of play.

```markdown
## Fantasy line
<what the player gets to be, in one line>

## Setting
<one sentence, with one unexpected detail>

## Theme phrase
<one phrase>

## Tone
Tone words: <three>. Anti-words: <three>.
This, not that: <two to five pairs, each with a sample string>.

## UI voice
<how buttons, errors, rewards and prompts speak; capitalisation; string-length limits per place>

## Naming rules
<one naming scheme; banned stock words; casing>

## Fiction of play
<what failure, scoring and progress mean in the fiction>

## Character cards
<each recurring face: role in play and in story, want, diction, banned words, sample line and bark>

## Glossary
| Term | Spelling and case | Meaning | Do not translate |
|---|---|---|---|

## Invariants it protects
<the narrative-related lines of the identity invariants, as written in vision.json>
```

Every rule is checkable on a string: the glossary and naming rules by a table lookup, the tone words by a sample string.
