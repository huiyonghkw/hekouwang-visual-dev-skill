# 发布检查清单

## 改动前

- [ ] 已说明仓库、文件、原因并得到用户确认。
- [ ] 已检查所有相关仓库 `git status`，记录并行修改。
- [ ] 已判断改动属于 Research、Content、Core 还是 Channel Design。
- [ ] 涉及第三方字体或素材时，已核对来源和分发许可。

## Visual Core

- [ ] 注册表 ID 唯一，默认主题存在，旧别名目标有效。
- [ ] Token、字体、组件和运行时没有回流到消费端形成副本。
- [ ] 安装脚本能把运行时安装到任意临时前缀。
- [ ] `core.py` 与 Core 单测通过。
- [ ] 版本、CHANGELOG 与兼容说明同步。

## Skills

- [ ] EP Research 只拥有事实与证据边界。
- [ ] Content Master 只输出内容合同，仍拥有文章母版网页。
- [ ] XHS Theme 只输出视觉计划并负责小红书装配与 QA。
- [ ] 没有 `*-xhs-spec`、`*-visual-spec` 等注册表外 ID。
- [ ] 每个被创建或修改的 Skill 分别通过 Skill Doctor。

## 验证

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_stack.py --isolated-install
```

- [ ] Content Master 单测通过。
- [ ] XHS Theme 单测与主题验证通过。
- [ ] 主 Harness working-tree、staged 或 CI 模式按任务需要通过。
- [ ] 新 EP 前向测试没有依赖旧 `~/.claude/skills/hekouwang-visual-core`。
- [ ] 自动检查和人工视觉检查分开记录。

## 推送

- [ ] 用户已明确要求 commit / push。
- [ ] 未使用 `--no-verify`。
- [ ] push 前重新检查工作树，未带入其他 Agent 的无关修改。
- [ ] GitHub About、README、版本和实际能力一致。
