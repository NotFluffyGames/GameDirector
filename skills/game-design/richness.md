# Richness

"Rich" made measurable, in three aspects. Every game needs at least one target per aspect, at or above the floor below; the design can and usually should ask for more.

| Aspect | Means | Floor | Example metric |
| --- | --- | --- | --- |
| **depth** | systems that change each other, so choices compound | at least 3 systems that interact, each one mattering | shift in the best bot policy's win rate, score or run length when each system is toggled off: ≥ 10 points (or 10%) for every system |
| **breadth** | enough distinct content that play doesn't repeat | content for 3 consecutive sessions without repeating the same set | count of distinct content per type (from the data files) against the design's counts; content seen per session by a bot |
| **variety** | two playthroughs differ in what happens and what works | two seeds share at most half of what they show, and more than one strategy wins | overlap of content or events between seeds ≤ 50%; at least 3 distinct bot strategies or builds each winning ≥ 15% of games |

Depth is measured with the systems' on/off toggles from the tuning knobs, which is one reason every system needs one. A system whose toggle changes nothing is not adding depth: cut it or connect it.

Breadth is cheap to fake with near-identical content. Count only pieces that play differently by the design's "what makes two pieces play differently" line, and back the count with a variety metric.
