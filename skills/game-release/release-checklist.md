# Release checklist

Each applicable line becomes a feature. The suggested verify kind is in brackets; where two are listed, use the first as `kind` and put both commands in `how`.

## Polish

- **Bugs**: every open bug ticket fixed or cut; a 2-hour fuzz run clean. [bot]
- **Game feel**: every core action gives visual and audio feedback within 100 ms (hit-stop, screen shake, particles, sound, as the tone allows). [capture + test]
- **Balance**: every proxy item passes with margin on the final content, re-measured with the verdict's bots. [bot]
- **Performance**: frame time, load time, memory and build size within the budget ADR on each target platform, measured on the heaviest scene. [sim or capture]
- **Final art and audio**: placeholders replaced per assets.md, matching design.md's style guide; every asset's license recorded. [capture + check]
- **Onboarding**: a new player reaches the core verb without outside help; the scripted new-player bot meets the onboarding threshold. [bot]
- **Accessibility baseline**: remappable controls; subtitles or captions for speech and key sounds; no information carried by colour alone; scalable or large-enough UI text; difficulty or assist options where the genre allows; pause anywhere in single-player; no flashing above 3 times per second. [check + capture]
- **Settings and saves**: settings persist; saves survive quit, crash and version upgrade. [replay]
- **Localization**: only when the pitch names more than one language; all strings externalized and the layout survives the longest translation. [capture]

## Release

- **Packaging**: the `package` command produces an artifact for each target platform, which launches and passes a smoke run. [check]
- **Versioning**: version number, changelog, a git tag for the release candidate. [check]
- **Credits and licenses**: credits screen and a licenses file covering every sourced asset and dependency. [check]
- **Store materials**: description copy from the pitch; screenshots from `capture` at chosen seeds; a trailer cut from captured footage, or a human queue entry for one. [check or human]
- **Human-only steps**, in the release wizard: store and developer accounts, signing keys and certificates, age ratings, platform certification or review submission, pricing, the launch button itself. [human]
- **Online games**: server deployment plan, monitoring, a patch cadence and a rollback path, as an ADR plus a wizard stage for credentials. [check + human]
