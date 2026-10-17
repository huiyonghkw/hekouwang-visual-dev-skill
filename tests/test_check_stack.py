import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_stack import (
    EXPECTED_THEMES,
    THEME_VARIANT_FAMILY,
    VARIANT_CHANNELS,
    check_stack,
)


def variant_of(theme: str) -> str:
    family = theme.split("-", 1)[0]
    allowed = THEME_VARIANT_FAMILY[family]
    return "readdy" if "readdy" in allowed else sorted(allowed)[0]


class StackFixture:
    def __init__(self, root: Path):
        self.core = root / "core"
        self.content = root / "content"
        self.xhs = root / "xhs"
        self.research = root / "research"
        for path in (self.core, self.content, self.xhs, self.research):
            path.mkdir(parents=True)

        (self.core / "assets/themes/legacy").mkdir(parents=True)
        themes = {
            name: {"label": name, "variant": variant_of(name)}
            for name in sorted(EXPECTED_THEMES)
        }
        registry = {
            "schema_version": 1,
            "version": "1.0.0",
            "default": "v2-mibai",
            "aliases": {"t2-keji-bai": "legacy:t2-keji-bai"},
            "themes": themes,
        }
        (self.core / "assets/theme_registry.json").write_text(
            json.dumps(registry), encoding="utf-8")
        (self.core / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        for name in themes:
            (self.core / f"assets/themes/{name}.css").write_text(":root{}", encoding="utf-8")
        (self.core / "assets/themes/legacy/t2-keji-bai.css").write_text(":root{}", encoding="utf-8")
        for channel in VARIANT_CHANNELS:
            variant_dir = self.core / "assets/components/variants" / channel
            variant_dir.mkdir(parents=True)
            for variant in {meta["variant"] for meta in themes.values()}:
                (variant_dir / f"{variant}.css").write_text(
                    ":root{}\n.cover-stage-v1{}", encoding="utf-8")
        (self.core / "README.md").write_text(
            "共享视觉核心；不决定某期说什么，也不决定渠道构图。", encoding="utf-8")

        (self.content / "contracts").mkdir()
        (self.content / "contracts/content-contract.schema.json").write_text(
            json.dumps({
                "type": "object",
                "additionalProperties": False,
                "required": ["version", "episode", "channel", "research_package_ref", "article_master_ref", "pages"],
                "properties": {
                    "version": {"const": "2"},
                    "episode": {}, "channel": {}, "research_package_ref": {}, "article_master_ref": {},
                    "pages": {"items": {"additionalProperties": False, "properties": {"id": {}, "role": {}, "core_message": {}}}},
                },
            }), encoding="utf-8")
        (self.content / "assets").mkdir()
        (self.content / "assets/validate_contract.py").write_text("# validator", encoding="utf-8")
        (self.content / "SKILL.md").write_text(
            "叙事真源；文章母版网页；输出 content-contract.json。", encoding="utf-8")

        (self.xhs / "contracts").mkdir()
        (self.xhs / "contracts/visual-plan.schema.json").write_text(
            json.dumps({
                "type": "object",
                "additionalProperties": False,
                "required": ["version", "episode", "channel", "theme", "content_contract_ref", "pages"],
                "properties": {
                    "version": {"enum": ["1", "1.1"]}, "episode": {}, "channel": {},
                    "theme": {}, "content_contract_ref": {},
                    "pages": {"items": {
                        "additionalProperties": False,
                        "required": ["id", "content_page_ref", "visual_role", "composition_intent", "fit_strategy"],
                        "properties": {
                            "id": {}, "content_page_ref": {}, "visual_role": {},
                            "composition_intent": {}, "fit_strategy": {},
                        },
                    }},
                },
            }),
            encoding="utf-8")
        (self.xhs / "scripts").mkdir()
        (self.xhs / "scripts/validate_visual_plan.py").write_text("# validator", encoding="utf-8")
        (self.xhs / "scripts/validate_build.py").write_text("# gate", encoding="utf-8")
        (self.xhs / "SKILL.md").write_text(
            "视觉装配与验收真源；消费内容合同；输出 visual-plan.json；Visual Core 是可复用运行时。", encoding="utf-8")

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

    def test_registry_missing_official_id_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            path = fixture.core / "assets/theme_registry.json"
            registry = json.loads(path.read_text(encoding="utf-8"))
            registry["themes"].pop("v6-yancai-hei")
            path.write_text(json.dumps(registry), encoding="utf-8")
            findings = self.run_fixture(fixture)
            self.assertTrue(any(item.code == "registry-missing-id" for item in findings))

    def test_ownership_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            (fixture.xhs / "SKILL.md").write_text("视觉也可以负责事实真源", encoding="utf-8")
            findings = self.run_fixture(fixture)
            self.assertTrue(any(item.code.startswith("xhs-owner-") for item in findings))

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

    def test_dependency_dirs_are_not_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            vendored = fixture.content / ".venv/lib/site-packages/rich/tree.py"
            vendored.parent.mkdir(parents=True)
            vendored.write_text("theme='monokai'\n", encoding="utf-8")
            self.assertEqual(self.run_fixture(fixture), [])

            owned = fixture.content / "scripts/tree.py"
            owned.parent.mkdir(parents=True)
            owned.write_text("theme='monokai'\n", encoding="utf-8")
            findings = self.run_fixture(fixture)
            self.assertTrue(any(item.code == "unknown-theme-reference" for item in findings))

    def test_theme_variant_family_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            path = fixture.core / "assets/theme_registry.json"
            registry = json.loads(path.read_text(encoding="utf-8"))
            registry["themes"]["v2-mibai"]["variant"] = "hud"
            path.write_text(json.dumps(registry), encoding="utf-8")
            findings = self.run_fixture(fixture)
            self.assertTrue(any(item.code == "theme-variant-family" for item in findings))

    def test_variant_channel_file_missing_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            (fixture.core / "assets/components/variants/xhs/editorial.css").unlink()
            findings = self.run_fixture(fixture)
            self.assertTrue(any(item.code == "variant-channel-missing" for item in findings))

    def test_orphan_variant_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = StackFixture(Path(tmp))
            (fixture.core / "assets/components/variants/web/rogue.css").write_text(
                ":root{}", encoding="utf-8")
            findings = self.run_fixture(fixture)
            self.assertTrue(any(item.code == "variant-orphan" for item in findings))


if __name__ == "__main__":
    unittest.main()
