# Visual Dev 版本历史与 Reference 覆盖矩阵

## 用途

本文件是视觉栈维护审计，不是主题设计指南。它把跨仓所有权、隔离安装、注册表、Token、字体和运行时兼容相关 commit 映射到当前 reference，避免把消费端的当期构图规则收回 Visual Core。

## Commit 演进

| Commit | 日期 | 主题 | 当前归档位置 | 状态 |
|---|---|---|---|---|
| `8e44d9a` | 2026-08-20 | 建立 Visual Dev Skill 与四层所有权 | `architecture.md`、`release-checklist.md` | 已完成 |
| `9c1915a` | 2026-08-20 | 跨仓检查、隔离安装与发布清单 | `release-checklist.md` 与 `scripts/check_stack.py` | 已完成 |
| 工作区待提交改动 | 2026-09-04 | Visual Plan 1.1 兼容与研究默认路径修正 | `CHANGELOG.md`、`scripts/check_stack.py`、`tests/` | 待独立提交，不能当作 Git 历史证据 |

## 主题覆盖矩阵

| 历史主题 | 当前真源 | 状态 | 说明 |
|---|---|---|---|
| 四层职责与所有权 | `architecture.md` | 保留 | EP Research、Content Master、Visual Core、Channel Design 各有唯一主人。 |
| `content-contract.json` / `visual-plan.json` 分层 | `architecture.md`、`release-checklist.md` | 保留 | 内容合同不拥有主题和构图；视觉计划不新增事实。 |
| 主题注册表、Token、字体与运行时 | Visual Core 仓库 | 保留 | 本 Skill 只维护边界和回归，不复制资源。 |
| 隔离安装与环境变量路径 | `release-checklist.md`、本 Skill | 保留并增强 | 不依赖 `~/.claude/skills` 中的隐式副本。 |
| 跨 Skill 重复资产与虚构 ID | `architecture.md`、`release-checklist.md` | 保留 | `*-xhs-spec`、`*-visual-spec` 等不是真实主题 ID。 |
| 生产硬门与内容研究合同 | 主 Harness / 对应 Skill | 跨层交接 | Visual Dev 检查边界，不重新实现 EP Research 或 Content Master 规则。 |

## 维护判定

1. 新增主题基础设施只有在至少两个通道稳定复用、没有携带当期事实和构图决策时才进入 Visual Core。
2. 当期文章图形留在 Content Master 或 EP 的 `_build.py`；小红书构图和平台 QA 留在 XHS Theme。
3. 工作区未提交的脚本或测试改动必须先单独核对，再决定是否纳入下一次版本历史；不能在审计中假装已经发布。
4. 修改 Visual Dev、Visual Core 或消费端契约后，运行各自单测、Skill Doctor、`check_stack.py --isolated-install` 和主 Harness；自动通过不替代真实目标尺寸人工视觉验收。
