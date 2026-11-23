# Polish checklist

Each applicable line becomes a feature in the `polish` milestone. A section named for a role is owned by it: the role goes in its features' `roles` beside `creative` (SKILL.md step 2). The design and playable-build sections say what theirs carry. The suggested verify kind is in brackets; where two are listed, use the first as `kind` and put both commands in `how`. **Taste** marks a call the person makes by A/B picks: verify `human`, the measured checks in acceptance beside what the person picks, and the pairs and the commands that run the checks in `how` (SKILL.md step 2). **Kept** marks a line that stays when its role is switched off.

## design

The design role judges these at the final verdict, from bot traces, never on a feature: their features carry `creative` and the roles of what they visibly change.

- **Balance**: every fun proxy and richness target passes with margin on the final content, re-measured with the verdict's bots. [bot]
- **Bugs**: every open bug ticket fixed or cut; a 2-hour crash and softlock fuzz run clean. [bot]

## feel

- **Feel pass**, one per core action: tuned one parameter at a time against the reference strips (the feel target's strips and the clips in `north_stars.feel`); input-to-response frames, windows and every feedback layer the feel sheet names, as tone allows (hit-stop, shake, particles, sound), within the sheet's targets in the event log. [replay + capture] A retune the sheet leaves to feel is its own feature: taste, its pairs shown as strips. [human + capture]

## art

- **Final art**: placeholders replaced per assets.md, in the art bible's style; every asset's source and license recorded. [capture + check]
- **Cohesion pass**: outliers normalised, outline and density unified, each capture beside the visual target; the palette within the bible's table. [capture]
- **Lighting or grade per area**. Taste. [human + capture]
- **Noise in the play layer**: nothing behind the play layer competes with the player, threats and pickups on the grayscale and thumbnail copies; each layer within the bible's value band. [capture]
- **Readability**: captures at the smallest target screen size pass the art bible's readability rules. [capture]

## audio

- **Final sound and music** for every screen and core action; every asset's source and license recorded. [check]
- **Missing-sound sweep**: every gameplay event in the event list maps to a sound that fires in the event log. [replay]
- **Variation and repetition**: each repeated event has the `audio` page's minimum variations, and no sample plays back to back beyond its limit. [replay]
- **Mix in the worst-case scene** (peak effects load): priority tiers and voice limits hold in the event log. Taste: the balance by ear. [human + replay]
- **Loudness**: integrated loudness and true peak within the `audio` page's targets in each named state with sound. [check]

## narrative

- **Tone pass**: every player-facing string keeps the glossary's spellings, uses no anti-word or banned word, and stays within its place's length limit. [check]
- **Continuity**: names, facts, and what failure, scoring and progress mean in the fiction agree across strings, screens and play. [check]
- **Localisation readiness**: every string in a table with an id; when the pitch names more than one language, the layout survives the longest translation. [check + capture]

## ux

- **Onboarding timing**: a new player reaches the core verb in their first minute without outside help; launch-to-control within the `onboarding` page's target; the scripted new-player bot meets the onboarding threshold. [bot + replay]
- **Screens**: the full screen flow from the `screens` page works from launch to quit: title, menus, settings, pause, results, quit. Kept. [replay or capture]
- **Accessibility settings**: remappable controls; subtitles or captions for speech and key sounds; no information carried by colour alone; scalable or large-enough UI text; difficulty or assist options where the genre allows; pause anywhere in single-player; no flashing above 3 times per second; and whatever else the `screens` page's accessibility minimum lists. [check + capture]
- **Settings and saves**: settings persist; saves survive quit, crash and a version change. Kept. [replay]
- **How to play**: in-game help or a short README section with the controls and how to start. Kept. [check]

## Playable build

No role owns these: their features carry `creative` and the roles of what they visibly change.

- **Performance**: frame time, load time, memory and build size within the budget ADR on each target platform, measured on the heaviest scene. [sim or capture]
- **Packaged build**: the `package` command produces a build per target platform this machine can build for; each launches without dev tools and plays from title screen to the end of a session in a smoke run. [check]
- **Credits and licenses**: a credits screen and a licenses file covering every sourced asset and dependency. [check]
