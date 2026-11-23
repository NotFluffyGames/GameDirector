"""Mechanical checks on the skills themselves: packaging, links, step criteria, and that every step the
state tool can hand out has a skill that knows how to do it.

Run: python3 -m unittest discover tests
"""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
TOOL = SKILLS / "game-setup" / "scripts" / "gamestate.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("gamestate", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return dict(re.findall(r"^([a-z-]+): (.*)$", m.group(1), re.M)) if m else {}


def outside_code(text):
    """The text with fenced code blocks blanked out, so templates inside them aren't read as live markdown."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def skill_dirs():
    return sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").is_file())


def markdown_files():
    return sorted(SKILLS.rglob("*.md")) + [ROOT / "README.md"]


class Packaging(unittest.TestCase):
    def test_plugin_lists_exactly_the_skill_folders(self):
        listed = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["skills"]
        self.assertEqual(sorted(listed), [f"./skills/{p.name}" for p in skill_dirs()])

    def test_every_skill_has_valid_frontmatter_and_agent_metadata(self):
        for d in skill_dirs():
            with self.subTest(skill=d.name):
                fm = frontmatter((d / "SKILL.md").read_text())
                self.assertEqual(fm.get("name"), d.name)
                self.assertTrue(re.fullmatch(r"[a-z0-9-]{1,64}", d.name))
                self.assertTrue(0 < len(fm.get("description", "")) <= 1024)
                self.assertNotRegex(fm["description"], r"[<>]")
                self.assertEqual(fm.get("disable-model-invocation"), "true")
                self.assertTrue((d / "agents" / "openai.yaml").is_file())


class Writing(unittest.TestCase):
    def test_relative_links_resolve(self):
        for md in markdown_files():
            for link in re.findall(r"\]\(([^)#\s]+)", outside_code(md.read_text())):
                if re.match(r"[a-z]+:", link):
                    continue
                with self.subTest(file=str(md.relative_to(ROOT)), link=link):
                    self.assertTrue((md.parent / link).exists())

    def test_every_numbered_step_ends_on_a_completion_criterion(self):
        for d in skill_dirs():
            text = outside_code((d / "SKILL.md").read_text())
            parts = re.split(r"^(#{2,3} \d+\. .*)$", text, flags=re.M)
            for heading, body in zip(parts[1::2], parts[2::2]):
                body = re.split(r"^#{1,3} ", body, flags=re.M)[0]
                with self.subTest(skill=d.name, step=heading):
                    self.assertIn("**Done when**", body)

    def test_tool_commands_named_in_the_skills_exist(self):
        commands = set(re.findall(r"^  ([a-z-]+) ", load_tool().__doc__, re.M))
        for md in markdown_files():
            for cmd in re.findall(r"gamestate\.py ([a-z][a-z-]*)", md.read_text()):
                with self.subTest(file=str(md.relative_to(ROOT)), command=cmd):
                    self.assertIn(cmd, commands)


class Steps(unittest.TestCase):
    """Every step the state tool can schedule must have a skill, and that skill must handle the step's mode."""

    def test_every_phase_has_a_skill(self):
        tool = load_tool()
        for phase in tool.PHASES:
            if phase in ("awaiting-human", "done"):
                continue
            skill = tool.PHASE_SKILLS.get(phase, f"game-{phase}")
            with self.subTest(phase=phase, skill=skill):
                self.assertTrue((SKILLS / skill / "SKILL.md").is_file())

    def test_every_scheduled_step_and_mode_is_handled_by_its_skill(self):
        tool = load_tool()
        source = TOOL.read_text()
        literals = re.findall(r'"game-([a-z]+)(?: ([a-z]+))?(?=["\s{])', source)  # the step strings it emits
        steps = {(skill, mode or None) for skill, mode in literals}
        steps |= {("verdict", scope) for scope in tool.SCOPES} | {("verdict", "answers")}
        steps |= {("consolidate", "production"), ("plan", "production")}
        for skill, mode in sorted(steps, key=str):
            with self.subTest(skill=skill, mode=mode):
                path = SKILLS / f"game-{skill}" / "SKILL.md"
                self.assertTrue(path.is_file())
                if mode:
                    self.assertIn(mode, path.read_text())


if __name__ == "__main__":
    unittest.main()
