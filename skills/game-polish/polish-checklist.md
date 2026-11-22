# Polish checklist

Each applicable line becomes a feature in the `polish` milestone. The suggested verify kind is in brackets; where two are listed, use the first as `kind` and put both commands in `how`.

## Feel and look

- **Game feel**: every core action gets the feedback the Feel pages name, within its response time (hit-stop, screen shake, particles, sound, as the tone allows). [capture + test]
- **Final art and audio**: placeholders replaced per assets.md, matching the style guide; music and sound for every screen and core action; every asset's source and license recorded. [capture + check]
- **Readability**: captures at the smallest target screen size pass the style guide's readability rules. [capture]

## Balance and depth

- **Balance**: every fun proxy and richness target passes with margin on the final content, re-measured with the verdict's bots. [bot]
- **Bugs**: every open bug ticket fixed or cut; a 2-hour crash and softlock fuzz run clean. [bot]

## Players

- **Onboarding**: a new player reaches the core verb in their first minute without outside help; the scripted new-player bot meets the onboarding threshold. [bot]
- **Screens**: the full screen flow from the Screens pages works from launch to quit: title, menus, settings, pause, results, quit. [replay or capture]
- **Accessibility baseline**: remappable controls; subtitles or captions for speech and key sounds; no information carried by colour alone; scalable or large-enough UI text; difficulty or assist options where the genre allows; pause anywhere in single-player; no flashing above 3 times per second. [check + capture]
- **Settings and saves**: settings persist; saves survive quit, crash and a version change. [replay]
- **Localization**: only when the pitch names more than one language; all strings externalized and the layout survives the longest translation. [capture]

## Playable build

- **Performance**: frame time, load time, memory and build size within the budget ADR on each target platform, measured on the heaviest scene. [sim or capture]
- **Packaged build**: the `package` command produces a build per target platform this machine can build for; each launches without dev tools and plays from title screen to the end of a session in a smoke run. [check]
- **Credits and licenses**: a credits screen and a licenses file covering every sourced asset and dependency. [check]
- **How to play**: a short README section or in-game help with controls and how to start. [check]
