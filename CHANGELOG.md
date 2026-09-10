# Changelog

## 未发布 · 2026-09-10 · 退役 V7/V8，矩阵收为 V1–V6

- `EXPECTED_THEMES` 与 Visual Core 1.0.6 对齐为 V1–V6 × 黑白共 12 主题。


## 未发布 · 2026-08-21 · Visual Plan v1.1 跨栈兼容

- 跨仓视觉栈检查同时接受视觉计划 v1 与 v1.1，避免 XHS 质量字段升级后被旧的 schema 常量门误判。

## 未发布 · 2026-08-20

- 跨仓门禁改为默认 fail-closed，不再依赖临时环境开关。
- 加强 Content Contract v2 / Visual Plan v1 的版本、必填字段、未知字段与所有权检查。
- 增加注册表缺 ID、所有权漂移正反例；主 Harness 可直接调用隔离安装检查。

## 0.1.0 · 2026-08-20

- 首次发布 `hekouwang-visual-dev-skill`。
- 定义 EP Research、Content Master、Visual Core、Channel Design 四层所有权。
- 增加跨仓所有权、合同拆分、注册表 ID、重复资产和隔离安装检查入口。
- 增加 Skill Doctor 与 push 前自检流程。
