# Fun proxies

Metrics a bot run, replay or headless simulation can measure in place of a fun statement. A proxy is evidence, not proof: it catches a game that is clearly not fun, and leaves the final word to human items and playtests. Pick thresholds from the pitch (session length, audience) and write them so a single number passes or fails.

| Fun statement | Proxy metric | Example threshold |
| --- | --- | --- |
| Matches stay tense to the end | score or health gap near the end; lead changes per match | gap within 10% in ≥ 40% of matches; ≥ 2 lead changes median |
| Comebacks are possible | win rate of the side behind at the midpoint | 20–40% |
| No dominant strategy | win rate of the best bot policy, character or build against the field; pick rate of the top option among winners | ≤ 60% win rate; ≤ 40% pick rate |
| Skill matters | win rate of a stronger bot (deeper search, better heuristic) against a weaker one | ≥ 70% |
| Luck doesn't decide it | outcome variance across seeds for the same bot pairing | the stronger bot wins on ≥ 70% of seeds |
| Choices are meaningful | viable actions per decision point (actions within X% of the best by bot evaluation); decisions per minute | ≥ 2 viable options median; ≥ 6 decisions/min for action games |
| The difficulty curve is smooth | progress reached by a fixed-skill bot; fail points per level | progress grows steadily; no level holds > 30% of fails |
| Sessions fit the target length | match or run duration distribution | median within the pitch's session length; p90 under 1.5× it |
| Onboarding is quick | time or ticks until a scripted new-player bot performs the core verb | under 30 seconds of game time |
| Runs feel different | distinct builds, routes or maps across seeds (set overlap) | ≤ 50% overlap between two random seeds |
| The core verb feels responsive | input-to-feedback latency in ticks; feedback events per core action | feedback within 100 ms; ≥ 1 visual and 1 audio cue |
| Nothing breaks | crashes, softlocks (no state change for N seconds while input arrives), errors during random-input fuzzing | zero over 30 minutes of fuzzing |

## What the roles review

A `review` item is judged by named roles from this build's captures, strips, event logs and bot traces, and fails only through a note anchored to something the person set: a calibration label, a reference they chose, a page rule. Write its statement so an anchor can decide it:

| Role | Example review item | `taste` |
| --- | --- | --- |
| `creative` | a fresh capture reads as this game, not its genre default; every identity invariant holds | true |
| `design` | no strategy dominates the bot traces; the difficulty curve follows the Systems pages | false |
| `feel` | every core action meets its feel sheet beside its reference clips | true |
| `art` | captures match the visual target; every colour role keeps to its use | true |
| `audio` | every gameplay event has its sound, with the variation and loudness the `audio` page sets | false |
| `narrative` | every player-facing string keeps the tone page's words, names and lengths | false |
| `ux` | a new player reaches the core verb in the first minute as the `onboarding` page lays out | true |

## What needs a human

Keep as `human` items: delight, humour, beauty, theme and emotional beats, "one more round", whether the controls feel good in the hands, whether the game sounds right, and anything about a real audience's taste. The roles' review items flag drift from the person's anchors; they don't score these.
