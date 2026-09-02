#!/usr/bin/env python3
"""检查 Hekouwang 视觉栈的跨仓所有权、合同和安装边界。"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


EXPECTED_THEMES = {
    "v1-keji-bai", "v1-keji-hei",
    "v2-mibai", "v2-mihei",
    "v3-caijing-bai", "v3-caijing-hei",
    "v4-boli-bai", "v4-boli-hei",
    "v5-zi-bai", "v5-zi-hei",
    "v6-yancai-bai", "v6-yancai-hei",
    "v7-qingning-bai", "v7-qingning-hei",
    "v8-naiyou-bai", "v8-naiyou-hei",
}
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".sh", ".css", ".html"}
PHANTOM_ID = re.compile(r"\bv[1-8]-[a-z0-9-]+-(?:xhs|visual)-spec\b")
THEME_ASSIGNMENT = re.compile(
    r"(?:theme\s*=|[\"']theme[\"']\s*:)\s*[\"']([^\"']+)[\"']"
)


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: str
    message: str


def finding(level: str, code: str, path: Path | str, message: str) -> Finding:
    return Finding(level, code, str(path), message)


def read_json(path: Path, findings: list[Finding], code: str) -> dict | None:
    if not path.is_file():
        findings.append(finding("error", code, path, "文件不存在"))
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(finding("error", code, path, f"JSON 无法读取：{exc}"))
        return None
    if not isinstance(value, dict):
        findings.append(finding("error", code, path, "JSON 顶层必须是对象"))
        return None
    return value


def text_files(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in {".git", "node_modules", "__pycache__", "output"} for part in path.parts):
            continue
        yield path


def check_registry(core: Path) -> tuple[list[Finding], set[str]]:
    findings: list[Finding] = []
    path = core / "assets/theme_registry.json"
    data = read_json(path, findings, "registry-missing")
    if data is None:
        return findings, set()
    if data.get("schema_version") != 1:
        findings.append(finding("error", "registry-schema-version", path, "schema_version 必须是 1"))
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        findings.append(finding("error", "registry-version", path, "version 必须是非空字符串"))
    version_file = core / "VERSION"
    if not version_file.is_file() or version_file.read_text(encoding="utf-8").strip() != version:
        findings.append(finding("error", "registry-version-drift", version_file, "VERSION 与注册表 version 不一致"))
    themes = data.get("themes")
    if not isinstance(themes, dict):
        findings.append(finding("error", "registry-shape", path, "themes 必须是对象"))
        return findings, set()
    actual = set(themes)
    missing = sorted(EXPECTED_THEMES - actual)
    extra = sorted(actual - EXPECTED_THEMES)
    if missing:
        findings.append(finding("error", "registry-missing-id", path, f"缺少规范主题：{missing}"))
    if extra:
        findings.append(finding("error", "registry-extra-id", path, f"出现注册表外主题：{extra}"))
    if data.get("default") not in actual:
        findings.append(finding("error", "registry-default", path, "default 未指向规范主题"))
    aliases = data.get("aliases", {})
    if not isinstance(aliases, dict):
        findings.append(finding("error", "registry-alias-shape", path, "aliases 必须是对象"))
    else:
        for alias, target in aliases.items():
            if not isinstance(alias, str) or not isinstance(target, str):
                findings.append(finding("error", "registry-alias-type", path, "别名与目标必须是字符串"))
            elif target.startswith("legacy:"):
                legacy = core / "assets/themes/legacy" / f"{target.removeprefix('legacy:')}.css"
                if not legacy.is_file():
                    findings.append(finding("error", "registry-alias-target", legacy, f"旧别名 {alias} 缺资源"))
            elif target not in actual:
                findings.append(finding("error", "registry-alias-target", path, f"别名 {alias} 指向未知主题 {target}"))
    for theme in sorted(actual):
        css = core / "assets/themes" / f"{theme}.css"
        if not css.is_file():
            findings.append(finding("error", "registry-theme-asset", css, f"主题 {theme} 缺 CSS"))
    return findings, actual | set(aliases if isinstance(aliases, dict) else {})


def check_phantom_ids(roots: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for root in roots:
        for path in text_files(root):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for match in PHANTOM_ID.finditer(text):
                findings.append(finding(
                    "error", "phantom-theme-id", path,
                    f"虚构主题 ID：{match.group(0)}；规范层级应使用独立 mode/profile 字段",
                ))
    return findings


def check_theme_references(roots: Iterable[Path], valid: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    for root in roots:
        for path in text_files(root):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for theme in THEME_ASSIGNMENT.findall(text):
                if theme not in valid and not theme.startswith("{") and "*" not in theme:
                    findings.append(finding(
                        "error", "unknown-theme-reference", path,
                        f"theme={theme!r} 不在 Visual Core 注册表或别名中",
                    ))
    return findings


def require_tokens(path: Path, required: Iterable[str], forbidden: Iterable[str], code: str) -> list[Finding]:
    findings: list[Finding] = []
    if not path.is_file():
        return [finding("error", f"{code}-missing", path, "所有权入口不存在")]
    text = path.read_text(encoding="utf-8")
    for token in required:
        if token not in text:
            findings.append(finding("error", f"{code}-required", path, f"缺少所有权声明：{token}"))
    for token in forbidden:
        if token in text:
            findings.append(finding("error", f"{code}-forbidden", path, f"命中越权表述：{token}"))
    return findings


def check_ownership(core: Path, content: Path, xhs: Path, research: Path) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(require_tokens(
        research / "SKILL.md",
        ["事实真源", "不实现视觉"],
        ["负责视觉计划", "负责最终标题"],
        "research-owner",
    ))
    findings.extend(require_tokens(
        content / "SKILL.md",
        ["叙事真源", "文章母版网页", "content-contract.json"],
        ["小红书视觉由本 Skill 独占", "Content Master 是事实真源"],
        "content-owner",
    ))
    findings.extend(require_tokens(
        xhs / "SKILL.md",
        ["视觉装配与验收真源", "visual-plan.json", "内容合同", "Visual Core 是可复用运行时"],
        ["事实真源", "选题、事实、文案、合规、来源内容由 hekouwang-content-master-skill 负责"],
        "xhs-owner",
    ))
    findings.extend(require_tokens(
        core / "README.md",
        ["共享视觉核心", "不决定某期"],
        ["文章叙事真源", "小红书构图真源"],
        "core-owner",
    ))
    return findings


def check_duplicate_assets(content: Path, xhs: Path) -> list[Finding]:
    findings: list[Finding] = []
    blocked = {
        content: [
            "assets/theme_registry.json", "assets/themes", "assets/fonts", "assets/runtime",
            "assets/components/components.css", "assets/components/variants",
        ],
        xhs: ["assets/theme_registry.json", "assets/themes", "assets/fonts", "assets/runtime", "assets/components"],
    }
    for root, relatives in blocked.items():
        for relative in relatives:
            path = root / relative
            if path.is_file() or (path.is_dir() and any(p.is_file() for p in path.rglob("*"))):
                findings.append(finding(
                    "error", "duplicate-core-asset", path,
                    "消费端仍保存 Visual Core 资源副本",
                ))
    return findings


def root_required(schema: dict) -> set[str]:
    required = schema.get("required", [])
    return set(required) if isinstance(required, list) else set()


def check_contract_split(content: Path, xhs: Path) -> list[Finding]:
    findings: list[Finding] = []
    content_path = content / "contracts/content-contract.schema.json"
    content_schema = read_json(content_path, findings, "content-contract-missing")
    if content_schema is not None:
        required = root_required(content_schema)
        properties = content_schema.get("properties", {})
        expected = {"version", "episode", "channel", "research_package_ref", "article_master_ref", "pages"}
        if not expected.issubset(required):
            findings.append(finding(
                "error", "content-contract-root", content_path,
                f"内容合同缺少根必填字段：{sorted(expected - required)}",
            ))
        version_schema = properties.get("version", {}) if isinstance(properties, dict) else {}
        if not isinstance(version_schema, dict) or version_schema.get("const") != "2":
            findings.append(finding("error", "content-contract-version", content_path, "内容合同 version 必须固定为字符串 2"))
        if "theme" in required or (isinstance(properties, dict) and "theme" in properties):
            findings.append(finding(
                "error", "content-contract-owns-theme", content_path,
                "内容合同不得定义 theme；主题属于渠道视觉计划",
            ))
        pages = properties.get("pages", {}) if isinstance(properties, dict) else {}
        items = pages.get("items", {}) if isinstance(pages, dict) else {}
        page_properties = items.get("properties", {}) if isinstance(items, dict) else {}
        for field in ("theme", "native_object", "relation", "visual_increment", "fit_strategy", "composition_intent", "asset_refs"):
            if isinstance(page_properties, dict) and field in page_properties:
                findings.append(finding(
                    "error", "content-contract-owns-visual", content_path,
                    f"内容合同仍包含视觉字段：{field}",
                ))
        if content_schema.get("additionalProperties") is not False or items.get("additionalProperties") is not False:
            findings.append(finding("error", "content-contract-open-shape", content_path, "内容合同根节点和页面必须拒绝未知字段"))
    visual_path = xhs / "contracts/visual-plan.schema.json"
    visual_schema = read_json(visual_path, findings, "visual-plan-missing")
    if visual_schema is not None:
        required = root_required(visual_schema)
        expected = {"version", "episode", "channel", "theme", "content_contract_ref", "pages"}
        if not expected.issubset(required):
            findings.append(finding(
                "error", "visual-plan-root", visual_path,
                f"视觉计划缺少根必填字段：{sorted(expected - required)}",
            ))
        properties = visual_schema.get("properties", {})
        version_schema = properties.get("version", {}) if isinstance(properties, dict) else {}
        if not isinstance(version_schema, dict) or version_schema.get("const") != "1":
            findings.append(finding("error", "visual-plan-version", visual_path, "视觉计划 version 必须固定为字符串 1"))
        pages = properties.get("pages", {}) if isinstance(properties, dict) else {}
        items = pages.get("items", {}) if isinstance(pages, dict) else {}
        page_required = root_required(items) if isinstance(items, dict) else set()
        expected_page = {"id", "content_page_ref", "visual_role", "composition_intent", "fit_strategy"}
        if not expected_page.issubset(page_required):
            findings.append(finding(
                "error", "visual-plan-page", visual_path,
                f"视觉计划页面缺少必填字段：{sorted(expected_page - page_required)}",
            ))
        page_properties = items.get("properties", {}) if isinstance(items, dict) else {}
        for field in ("title", "copy", "core_message", "locked_fact_ids", "evidence_refs", "source_refs", "non_rewrite", "compliance_notes"):
            if isinstance(page_properties, dict) and field in page_properties:
                findings.append(finding(
                    "error", "visual-plan-owns-content", visual_path,
                    f"视觉计划仍包含内容字段：{field}",
                ))
        if visual_schema.get("additionalProperties") is not False or items.get("additionalProperties") is not False:
            findings.append(finding("error", "visual-plan-open-shape", visual_path, "视觉计划根节点和页面必须拒绝未知字段"))
    for path, code in (
        (content / "assets/validate_contract.py", "content-contract-validator"),
        (xhs / "scripts/validate_visual_plan.py", "visual-plan-validator"),
        (xhs / "scripts/validate_build.py", "dual-contract-build-gate"),
    ):
        if not path.is_file():
            findings.append(finding("error", code, path, "合同存在但缺少可执行校验器"))
    return findings


def import_smoke(module_path: Path, env: dict[str, str]) -> tuple[bool, str]:
    code = (
        "import importlib.util, pathlib; "
        f"p=pathlib.Path({str(module_path)!r}); "
        "s=importlib.util.spec_from_file_location('visual_stack_smoke', p); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m)"
    )
    result = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True, env=env)
    return result.returncode == 0, (result.stderr or result.stdout).strip()


def check_isolated_install(core: Path, content: Path, xhs: Path) -> list[Finding]:
    findings: list[Finding] = []
    installer = core / "scripts/install.sh"
    if not installer.is_file():
        return [finding("error", "isolated-installer", installer, "缺少可指定 --prefix 的安装脚本")]
    with tempfile.TemporaryDirectory(prefix="hkw-visual-core-") as tmp:
        prefix = Path(tmp) / "runtime"
        result = subprocess.run(
            ["bash", str(installer), "--prefix", str(prefix)],
            text=True, capture_output=True,
        )
        if result.returncode != 0:
            return [finding(
                "error", "isolated-install", installer,
                f"隔离安装失败：{(result.stderr or result.stdout).strip()}",
            )]
        core_entry = prefix / "core.py"
        if not core_entry.is_file():
            findings.append(finding("error", "isolated-layout", core_entry, "安装后缺 core.py"))
            return findings
        env = os.environ.copy()
        env["HEKOUWANG_VISUAL_CORE_DIR"] = str(prefix)
        env.pop("PYTHONPATH", None)
        validate = subprocess.run(
            [sys.executable, str(core_entry)], text=True, capture_output=True, env=env,
        )
        if validate.returncode != 0:
            findings.append(finding(
                "error", "isolated-core-validation", core_entry,
                (validate.stderr or validate.stdout).strip(),
            ))
        for module in (content / "assets/build_lib.py", xhs / "assets/xhs_kit.py"):
            ok, output = import_smoke(module, env)
            if not ok:
                findings.append(finding(
                    "error", "isolated-consumer-import", module,
                    f"消费端未能从隔离 Core 导入：{output}",
                ))
    return findings


def check_stack(
    core: Path,
    content: Path,
    xhs: Path,
    research: Path,
    isolated_install: bool = False,
) -> list[Finding]:
    findings, valid = check_registry(core)
    roots = (core, content, xhs, research)
    findings.extend(check_phantom_ids(roots))
    if valid:
        findings.extend(check_theme_references((core, content, xhs), valid))
    findings.extend(check_ownership(core, content, xhs, research))
    findings.extend(check_duplicate_assets(content, xhs))
    findings.extend(check_contract_split(content, xhs))
    if isolated_install:
        findings.extend(check_isolated_install(core, content, xhs))
    return findings


def default_path(env_name: str, relative: str) -> Path:
    configured = os.environ.get(env_name)
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / relative).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, default=default_path(
        "HEKOUWANG_VISUAL_CORE_REPO", "Dashboard/Github/hekouwang-visual-core"))
    parser.add_argument("--content", type=Path, default=default_path(
        "HEKOUWANG_CONTENT_SKILL_DIR", ".claude/skills/hekouwang-content-master-skill"))
    parser.add_argument("--xhs", type=Path, default=default_path(
        "HEKOUWANG_XHS_SKILL_DIR", ".claude/skills/hekouwang-xhs-theme-skill"))
    parser.add_argument("--research", type=Path, default=default_path(
        "HEKOUWANG_RESEARCH_SKILL_DIR",
        "Dashboard/Github/hekouwang-content-growth-engine-agent/.agents/skills/hekouwang-ep-research-skill"))
    parser.add_argument("--isolated-install", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = check_stack(
        args.core.resolve(), args.content.resolve(), args.xhs.resolve(), args.research.resolve(),
        isolated_install=args.isolated_install,
    )
    errors = [item for item in findings if item.level == "error"]
    if args.json:
        print(json.dumps({
            "ok": not errors,
            "errors": len(errors),
            "findings": [asdict(item) for item in findings],
        }, ensure_ascii=False, indent=2))
    elif errors:
        print(f"FAIL: 视觉栈检查发现 {len(errors)} 个错误")
        for item in errors:
            print(f"- [{item.code}] {item.path}: {item.message}")
    else:
        print("OK: 视觉栈所有权、合同、注册表与安装边界通过")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
