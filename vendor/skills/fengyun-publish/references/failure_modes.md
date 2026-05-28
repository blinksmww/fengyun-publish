# Failure Modes — 失败回退总表 + 配套脚本 + 调试 hook

> 主体跳转:`SKILL.md` 失败行为概览
> 本文件来源:SKILL.md.pre-w1-bak L1373-1389 + L1414-1423 + L1438-1445,W1 纯拆分不改字段

---

## 错误处理 / 降级总表

| 故障 | 降级 |
|---|---|
| huashu-perspective skill 不存在 | Track B 跳过,听 C verdict + 标 degraded |
| content-judge skill 不存在 | Track C 跳过,听 B verdict + 标 degraded |
| B 和 C 都不存在 | 无灵魂底线,revise 改稿重试(critic_vote.py gate_tree;不 abort)|
| wangxiaobo skill 不存在 / 报错 | Step 5 跳过,记 degraded |
| aihot 拿不到数据 | 全部走 WebSearch |
| baoyu-cover-image 不存在 / 出图失败 | 用 baoyu-imagine 备选,再不行用 placeholder(assets/placeholder-sketch.png)自动兜底,无人工 |
| `post_fengyun_publish.py` 推送失败 | 留本地 HTML preview + 错误日志,不重试 |
| 改稿到隐藏 3 轮天花板还没双过 | critic_vote.py 自动 `force_ship`(强制 ship + WARN 标记,全自动闭环,W2.C6)|
| 末轮 lint 命中 R18-P0(明确自指 AI 身份)| revise 自动删段;改到天花板仍 P0 → `aborted_r18` 自动终止(ERROR 日志,不 ship,无人工)|
| 任一轮 lint 命中 R18-P1 / P2 | 不阻断,走 gate tree;r18_dashboard 周报会告警是否需修 L1 writer |
| 字数 lint 反复过不了(R12 振荡) | 中止,fengyun-writer 写不出 4000-5000 字深度文是 deeper issue |
| corpus 检索不到主题 | 不视为故障,记 note 即可 |

## 配套脚本

- `tools/ship.py` — orchestrator stub,接受 topic 参数,在 console 打印每一步该 invoke 哪个 skill / 该跑哪个 .py。不全自动跑 Claude skill(那些必须 Claude 主导),只做可机械化的事 + 流程提示
- `tools/post_fengyun_publish.py` — 由 `post_fengyun_v3.py` 通用化,接受 DRAFT_PATH 命令行参数
- `tools/critic_vote.py` — 读 huashu(B)+ content-judge(C)双轨 verdict,双轨 gate_tree + 隐藏天花板 force_ship 决议(W2.C6 删 Track A score_draft)
- `tools/headless_ship.ps1` / `tools/headless_ship.bat`(Phase 7 新增)— headless 全自动入口,用 `claude -p` 触发本 skill。用法:
  ```powershell
  .\tools\headless_ship.ps1 -Topic "ship 一篇关于 Anthropic 一周 7 件事的文章"
  ```
  或双击 `.bat` 在 cmd 里跑。可配 Windows Task Scheduler 实现 cron 全自动。

## 调试 hook

如果跑挂了,先看:

1. `output/runs/YYYYMMDD-<slug>.json` 看到第几步 fail
2. `output/drafts/*.lint.json` 看 lint 报告
3. `.env` 里 `WECHAT_APPID` / `WECHAT_SECRET` 有没有(post_fengyun_publish.py 需要)
4. `D:\Dev\ai-wechat-pipeline\style_match_features.parquet` / `viral_design_features.parquet` 在不在(sop_v2_1.py 需要)
