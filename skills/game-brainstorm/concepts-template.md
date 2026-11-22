# Concepts template

Copy into `docs/game/concepts.md`. Keep the `##` headings and the `### C<n>:` concept headings exactly; `gamestate.py gate` looks for them.

```markdown
# Concepts

Seed: <one line from seed.md>. Fixed by the seed: <what must stay true>. Open: <what the seed leaves open>.

## Concepts

### C1: <name>

- **Hook**: <one sentence a player would repeat to a friend>
- **Core verb**: <what the player does most>
- **Core loop**: <one sentence: the repeated action and what it feeds>
- **Target feeling**: <challenge, tension, discovery, mastery, expression, fellowship, ...>
- **References**: <2-3 games, and what this takes from each>
- **Richness sources**: <which systems change each other; which content scales from kit pieces; what makes two runs differ>
- **Biggest risk**: <the thing most likely to make it not fun or not buildable>

### C2: <name>

...

## Scores

| Concept | Fun | Richness | Fit | Agent-buildable | Risk | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | 4: ... | 3: ... | 5: ... | 4: ... | 3: ... | |

## Prototypes

### C1

Policies: random, greedy. Games: 50 seeded.

| Measure | Result |
| --- | --- |
| Decision density | 2.4 viable options per turn (median) |
| Skill | greedy beats random in 88% of games |
| Dominance | most-used action was best 41% of the time |
| Endings | median 34 turns; 12% ended in a stalemate |

Open risks: <what the prototype could not show>.

## Choice

C1, because <evidence>. Still unproven: <...>. Borrow from C3: <...>.
```
