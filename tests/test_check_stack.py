import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_stack import EXPECTED_THEMES, check_stack


class StackFixture:
    def __init__(self, root: Path):
        self.core = root / "core"
        self.content = root / "content"
        self.xhs = root / "xhs"
        self.research = root / "research"
        for path in (self.core, self.content, self.xhs, self.research):
            path.mkdir(parents=True)

        (self.core / "assets/themes/legacy").mkdir(parents=True)
        themes = {name: {"label": name} for name in sorted(EXPECTED_THEMES)}
        registry = {
            "default": "v2-mibai",
            "aliases": {"t2-keji-bai": "legacy:t2-keji-bai"},
            "themes": themes,
        }
        (self.core / "assets/theme_registry.json").write_text(
            json.dumps(registry), encoding="utf-8")
        for name in themes:
            (self.core / f"assets/themes/{name}.css").write_text(":root{}", encoding="utf-8")
        (self.core / "assets/themes/legacy/t2-keji-bai.css").write_text(":root{}", encoding="utf-8")
        (self.core / "README.md").write_text(
            "共享视觉核心；不决定某期说什么，也不决定渠道构图。", encoding="utf-8")

        (self.content / "contracts").mkdir()
        (self.content / "contracts/content-contract.schema.json").write_text(
            json.dumps({"type": "object", "required": ["episode", "pages"],
                        "properties": {"episode": {}, "pages": {}}}), encoding="utf-8")
        (self.content / "SKILL.md").write_text(
            "叙事真源；文章母版网页；输出 content-contract.json。", encoding="utf-8")

        (self.xhs / "contracts").mkdir()
        (self.xhs / "contracts/visual-plan.schema.json").write_text(
            json.dumps({"type": "object",
                        "required": ["theme", "content_contract_ref", "pages"],
                        "properties": {"theme": {}, "content_contract_ref": {}, "pages": {}}}),
            encoding="utf-8")
        (self.xhs / "SKILL.md").write_text(
            "视觉装配与验收真源；消费内容合同；输出 visual-plan.json。", encoding="utf-8")

        (self.research / "SKILL.md").write_text(
            "EP Research 是事实真源，不实现视觉。", encoding="utf-8")


class CheckStackTest(unittest.TestCase):
    def run_fixture(self, fixture: StackFixture):
        return check_stack(
            fixture.core, fixture.content, fixture.xhs, fixture.research,
            isolated_install=False,
        )

    def test_clean_stack_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            self.assertEqual(self.run_fixture(fixture), [])

    def test_phantom_spec_id_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            with (fixture.xhs / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write("\n`v1-keji-bai-xhs-spec`\n")
            findings = self.run_fixture(fixture)
            self.assertTrue(any(item.code == "phantom-theme-id" for item in findings))

    def test_content_contract_cannot_own_theme(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            path = fixture.content / "contracts/content-contract.schema.json"
            path.write_text(json.dumps({
                "type": "object",
                "required": ["episode", "theme", "pages"],
                "properties": {"episode": {}, "theme": {}, "pages": {}},
            }), encoding="utf-8")
            findings = self.run_fixture(fixture)
            self.assertTrue(any(item.code == "content-contract-owns-theme" for item in findings))

    def test_duplicate_runtime_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            duplicate = fixture.xhs / "assets/runtime/shoot.js"
            duplicate.parent.mkdir(parents=True)
            duplicate.write_text("// duplicate", encoding="utf-8")
            findings = self.run_fixture(fixture)
            self.assertTrue(any(item.code == "duplicate-core-asset" for item in findings))

    def test_wildcard_theme_example_is_not_an_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            with (fixture.xhs / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write("\n示例：theme='v*-*'\n")
            self.assertEqual(self.run_fixture(fixture), [])


if __name__ == "__main__":
    unittest.main()
