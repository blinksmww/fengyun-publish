# NOTICE

`fengyun-publish` — end-to-end AI 公众号 ship pipeline
公众号「研究 Agent 的云」· 笔名「风云」

---

## 项目背景

本仓库为「研究 Agent 的云」公众号背后的自动化发布管道,从信源采集 → 选题
→ 撰写 → 多 perspective critic → 排版 → 配图 → 发布,全流程在 Claude Code
+ Agent SDK 上跑通。代码以 MIT 协议开放,欢迎围观、复用与改进。

## 关于本仓库的几点说明

1. **不附带 KOL 语料**:原项目的 `corpus/` 目录包含第三方 KOL 文章节选
   (用于本机风格分析),已在本开源版本中**完整移除**。任何想复现风格逆向
   流程的用户,请自行抓取并遵守对应版权。

2. **不附带历史草稿**:`output/drafts/` 与 `output/research/` 内的过程文档
   不在本仓库公开,仅保留 `output/diagrams/` 架构图与少量公开 patch。

3. **不附带凭证**:`.env` / WeChat token / API key 等敏感文件已通过
   `.gitignore` 排除;`.env.example` 给出占位符模板。**首次运行前请
   自行准备凭证**(详见 `SECURITY.md` 与 `README.md`)。

## 致谢

本管道的若干设计思路来自下列开源工作者的公开内容与生态产出,在此一并致谢
(以下命名仅为感谢,不代表对方为本仓库背书):

- **数字生命卡兹克** — 公众号长文风格与「横纵分析」方法论的早期参照
- **宝玉** — Anthropic / OpenAI 译文体系与 baoyu-* 系列 skill 的开源
- **花叔** — 一人公司视角、shipping velocity 哲学、`huashu-perspective` 灵感
- **赛博禅心** — AI 资讯播报体例参照

skill 生态参考:
- [Anthropic Claude Code Skills](https://docs.claude.com/en/docs/claude-code/skills)
- [khazix-skills](https://github.com/Khazix/khazix-skills)(MIT)
- [baoyu-skills](https://github.com/baoyu) 系列
- 花叔开源的 `huashu-skills`(8k+ star)

## 联系方式

  Email   : 2330304961@qq.com
  WeChat  : FengYunAgent
  公众号  : 研究 Agent 的云

欢迎在 GitHub Issues 提问、Pull Request 共建。
