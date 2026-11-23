# Narrative: review checklist

Mark each line passed, a note, or `not-assessed` with the reason. In a feature review a note is `blocking` only when a measured check written into the feature's frozen acceptance fails at the quality bar in `vision.json` `slice.quality_bar`; every other note is `advisory`, and in a verdict or polish-scope review all are. A page rule is the anchor; it decides whether a note can fail an item through its `item`, never its severity. A `placeholder` bar gets no tone judgment of placeholder text. Read the `review` items that name `narrative` first.

## Checked first (from the string tables)

- Glossary: each term appears as the glossary spells and cases it; list each variant found.
- Banned words: no banned stock word or anti-word from the page appears in the strings.
- String length: each string is within the page's limit for its place (button, title, tooltip, subtitle).
- Subtitle coverage: every voiced line has a subtitle, where voiced lines exist.

## Judged (against the page, from the text dump)

- Naming: names of characters, places and items fit the page's naming scheme.
- Strings live in a table with IDs: compare the text dump with the tables; a string only in the dump is a note.
- UI text keeps the UI voice, and its words sit within the tone words.
- No line uses an anti-word or its register.
- Barks: each recurring face's barks keep its character card's diction and avoid its banned words; repeated barks don't explain what the player can see.
- Fiction against play: what failure, scoring and progress mean in the fiction matches what the build does; a mismatch is a note with both quoted.
- Only what a page rule settles; the rest is `not-assessed` with that reason.

## Needs the person

- Whether players can restate the premise: never a note.
- Taste in prose beyond the page's rules: never a note; narrative is not calibrated by labels.
