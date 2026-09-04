# hekouwang-visual-dev-skill

维护会勇禾口王共享视觉内核的 Agent Skill。

它负责判断视觉能力应该落在哪一层，并对 `hekouwang-visual-core`、`hekouwang-content-master-skill`、`hekouwang-xhs-theme-skill` 和 EP Research 的交接契约做跨仓回归。它不是主题资源仓，也不直接制作某一期 EP。

## 为什么需要它

当主题、字体、组件和截图脚本分别复制在多个 Skill 中时，任何一次“统一升级”都可能产生三套真源：

- Content Master 误把小红书视觉实现收回去；
- XHS Theme 同时维护主题资源和渠道构图，入口越来越重；
- Visual Core 虽然存在，消费端仍保留重复字体、Token 和运行时；
- 文档使用了注册表中不存在的 `*-spec` 内部 ID；
- Skill Doctor 全部高分，跨 Skill 行为仍然漂移。

本 Skill 把这些问题变成可执行的所有权判断和回归检查。

## 仓库关系

```text
EP Research ──锁定事实──▶ Content Master ──内容合同──▶ Channel Design
                                  │                        │
                                  │ 文章网页决策           │ 视觉计划 / 构图 / QA
                                  └────────┬───────────────┘
                                           ▼
                               hekouwang-visual-core
                         注册表 / Token / 字体 / 基础组件 / 运行时

hekouwang-visual-dev-skill：维护上面这套边界并执行跨仓回归
```

四层职责的完整定义见 [`references/architecture.md`](references/architecture.md)；版本演进与 reference 覆盖见 [`references/version-history-and-coverage.md`](references/version-history-and-coverage.md)。

## 适用场景

- 新增或修改 V1–V8 主题及黑白两极；
- 调整共享 Token、字体合同、基础组件、`fit.js` 或 `shoot.js`；
- 把 Content Master / XHS Theme 中的重复视觉资产迁移到 Core；
- 检查 `content-contract.json` 与 `visual-plan.json` 是否重新混在一起；
- 检查文档、脚本和合同引用的主题 ID 是否真实存在；
- 发布 Visual Core 或相关 Skill 前做跨仓回归。

不适用于：撰写文章、建立 EP 研究包、制作某期小红书组图、决定具体页面构图或执行平台发布。

## 安装

安装为可发现 Skill：

```bash
git clone https://github.com/huiyonghkw/hekouwang-visual-dev-skill.git \
  ~/.agents/skills/hekouwang-visual-dev-skill
```

也可以安装到当前 Agent 的 Skill 目录。目录中必须保留 `SKILL.md`、`references/` 和 `scripts/`。

首次克隆后安装仓库内的 push 前检查：

```bash
bash scripts/install-hooks.sh
```

## Visual Core 路径

Visual Core 的源码仓与运行时安装目录分离：

```text
源码仓：~/Dashboard/Github/hekouwang-visual-core
运行时：~/.hekouwang/visual-core
```

推荐显式设置：

```bash
export HEKOUWANG_VISUAL_CORE_REPO="$HOME/Dashboard/Github/hekouwang-visual-core"
export HEKOUWANG_VISUAL_CORE_DIR="$HOME/.hekouwang/visual-core"
```

测试和 CI 应把 `HEKOUWANG_VISUAL_CORE_DIR` 指向临时目录，证明适配器没有偷偷依赖 `~/.claude/skills`。

## 跨仓检查

完整调用：

```bash
python3 scripts/check_stack.py \
  --core "$HEKOUWANG_VISUAL_CORE_REPO" \
  --content "$HEKOUWANG_CONTENT_SKILL_DIR" \
  --xhs "$HEKOUWANG_XHS_SKILL_DIR" \
  --research "$HEKOUWANG_RESEARCH_SKILL_DIR" \
  --isolated-install
```

检查内容：

1. Visual Core 注册表必须是 16 个规范主题，默认主题和旧别名都能解析；
2. Content Master / XHS Theme 不得继续保存主题、字体、注册表与截图运行时副本；
3. EP Research、Content Master、Visual Core、Channel Design 的所有权声明不能互相覆盖；
4. `content-contract.json` 不含主题与构图决策，`visual-plan.json` 才拥有 `theme`；
5. `*-xhs-spec`、`*-visual-spec` 等虚构 ID 必须失败；
6. Core 必须能安装到临时目录，并被两个消费端通过环境变量加载。

输出 JSON：

```bash
python3 scripts/check_stack.py --json
```

## 自检

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 ~/.claude/skills/hekouwang-claude-skill-doctor-skill/check.py .
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

Skill Doctor 负责单个 Skill 的触发、篇幅、渐进披露与可移植性；`check_stack.py` 负责它无法覆盖的跨仓所有权与运行时契约。两者不能互相替代。

## 修改原则

- 可复用资源进入 Visual Core；当期内容图形留在 EP 的 `_build.py`。
- Content Master 决定文章叙事与文章母版网页，不决定小红书构图。
- XHS Theme 决定小红书视觉计划、构图实现和 QA，不重新写事实或文案。
- 主题调用只使用注册表 ID，例如 `v1-keji-bai`；“视觉规范”“图组规范”用模式表达，不拼接到 ID。
- 自动检查通过不等于视觉通过；真实目标尺寸仍需人工验收。

发布流程见 [`references/release-checklist.md`](references/release-checklist.md)。

## GitHub About 建议

Description：

> 维护 Hekouwang Visual Core 的 Agent Skill：主题注册表、设计 Token、字体合同、跨渠道所有权与隔离安装回归。

Topics：`agent-skills`、`visual-system`、`design-tokens`、`content-workflow`、`claude-code`、`codex`、`testing`。

## 许可证

代码与文档使用 [MIT-0](LICENSE)。Visual Core 中的第三方字体、图标和其它视觉资产遵循各自许可证，不因本 Skill 的许可证而改变。
