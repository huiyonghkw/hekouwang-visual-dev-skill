---
name: hekouwang-visual-dev-skill
description: 维护会勇禾口王共享视觉内核及其跨 Skill 契约。当用户要求新增或调整 V1–V8 主题、设计 Token、字体合同、通道组件、fit/shoot 运行时，或检查 Visual Core、Content Master、XHS Theme 之间的所有权与注册表漂移时使用。不用于制作某一期 EP、撰写内容或直接生成渠道图片。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# 禾口王视觉内核开发

维护 `hekouwang-visual-core` 及其消费端适配器，让共享资源只有一个真源，同时保留 Content Master 与各渠道 Design Skill 的表达决策权。

## 所有权边界

| 层 | 唯一职责 |
|---|---|
| EP Research | 事实、证据、数据口径、判断边界与风险 |
| Content Master | 叙事、文案、来源与合规表达、文章母版网页、`content-contract.json` |
| Visual Core | 主题注册表、Token、字体合同、可复用基础组件、`fit` / `shoot` 运行时 |
| Channel Design | 渠道视觉计划、构图实现、平台适配与视觉验收；XHS 拥有 `visual-plan.json` |

Visual Core 不决定某期说什么，也不决定某页如何构图。只有被两个以上通道稳定复用、且不含 EP 内容判断的能力，才进入 Core。

## 维护流程

1. 读取 [references/architecture.md](references/architecture.md)，先判断改动属于 Core、Content Master 还是渠道层；需要追溯覆盖时再读 [references/version-history-and-coverage.md](references/version-history-and-coverage.md)。
2. 检查相关仓库 `git status`；保留用户和并行 Agent 的修改，不重置或覆盖。
3. 修改注册表时只使用其中真实存在的规范 ID；“视觉规范”“图组规范”是调用模式，不另造 `*-spec` ID。
4. Core 源码改完先在隔离前缀安装，再让 Content Master 与 XHS 适配器通过 `HEKOUWANG_VISUAL_CORE_DIR` 冒烟导入。
5. 运行 `python3 scripts/check_stack.py`，检查隔离安装、所有权、重复资产、合同拆分和注册表引用。
6. 任何 Skill 被创建或修改，都分别运行用户的 `hekouwang-claude-skill-doctor-skill/check.py`；Core 本身不是 Skill，使用自身单测与验证器。
7. 按 [references/release-checklist.md](references/release-checklist.md) 完成检查。未经用户明确授权，不提交或推送。

## 路径约定

优先使用环境变量，不把宿主目录写死：

- `HEKOUWANG_VISUAL_CORE_REPO`：Visual Core 源码仓。
- `HEKOUWANG_VISUAL_CORE_DIR`：已安装运行时；默认 `~/.hekouwang/visual-core`。
- `HEKOUWANG_CONTENT_SKILL_DIR`、`HEKOUWANG_XHS_SKILL_DIR`、`HEKOUWANG_RESEARCH_SKILL_DIR`：集成检查目标。
- `HEKOUWANG_SKILL_DOCTOR_DIR`：Skill Doctor 目录。

旧路径 `~/.claude/skills/hekouwang-visual-core` 只作迁移兼容，不能继续作为新文档的默认路径。

## 完成门

只有以下结果同时成立，才可宣称视觉栈维护完成：

- Core 注册表、安装测试和单测通过；
- 跨 Skill 所有权、合同拆分、重复资产和注册表 ID 检查通过；
- 每个被修改的 Skill Doctor 通过；
- Content Master、XHS Theme 与主 Harness 的相关测试通过；
- 至少一次隔离环境前向测试通过，自动检查与人工视觉检查分开报告。

README 面向安装者和维护者；运行时架构细节只按需读取 references，不复制回本入口。
