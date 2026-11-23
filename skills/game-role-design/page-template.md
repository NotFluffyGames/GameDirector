# Design: living pages

The design role writes three pages, one per subject: Mechanics, Systems and Content. Keep each under the wiki's split rule.

## Mechanics (one section per verb)

```markdown
### <verb>
- Decision: <what the player chooses, and the cost of each option>
- Rules and states: <...>
- Tunables: <name = default, in the tunables file>
- Edge cases and tests: <...>
```

## Systems (one section per system, plus one standards sheet)

```markdown
### <system>
- Purpose and pillar: <...>
- Inputs and outputs to other systems: <...>
- Sources and sinks: <resource: what adds it, what spends it, per minute>
- Tunables: <name = default>
- Check: <a number a bot run can fail, e.g. "median run lasts 8-12 minutes">
```

The standards sheet lists the global numbers every system shares (speed, damage and health scales, time units).

## Content (one row per piece)

| Piece | Role | Counter | Pressure | Introduced at |
|---|---|---|---|---|

Role is one verb-phrase a player could say aloud. A piece without a counter, or two pieces with the same role and counter, is a review note. Levels get a beat chart: time-ordered beats with intensity, the mechanic introduced or tested, and the reward.
