# Wave 6(重定义): tool 真 CLI 补齐 + ship.py 编排器 W3-supersede 记录

> **⚠️ W6 重定义(2026-05-27,用户拍板 Option 1)**:原 §0/§5/ARCH 的 W6 =「Agent SDK 重写 ship.py(orchestrator-worker)」**前提已失效** —— **不存在 `tools/ship.py`**(唯一 ship.py 是 `backups/2026-05-24-round5-baseline/` 的 pre-refactor 备份),且 **W3 已用 `/ship` slash command + 5 个 subagent 实现了 orchestrator-worker 模式**(slash = orchestrator,subagent = worker,native Claude Code)。原计划 2026-05-26 写于 W3 执行之前。
>
> **决策(reviewer/Musk 复核)**:① 承认 W3 的 `/ship` slash + subagents 已满足决策 #4 的 orchestrator-worker(invariant #2 统一语言:不再建竞争性 Python ship.py)② headless Python ship.py(claude-agent-sdk)主要为 **paused 的 cloud/cron 24/7** 服务 —— invariant #4「0 消费者 = 0 生产」:headless 消费者现在不存在(cloud 暂停,SDK 独立计费 2026-06-15 才生效)→ **延到 cloud 阶段** ③ W6 重定义为「**补齐 W5 欠的 tool 真 CLI**」+ 记录 supersession。

---

## 物理目的(一句话)

把 W5 因「doc-only」而留作 `python -c` 过渡的 ~9 个无 CLI 工具补上**真 argparse CLI**(test-first),然后把 SKILL/references/WRITE_AGENT 里的 `python -c` 一行**回写成干净的 `python tools/X.py --flag` 命令**;并在 plan 文档记录「ship.py 编排被 W3 slash 取代」。

---

## scope:为什么是 ~9 个工具不是 4 个

W5 §4.5 follow-up 名义上写「4 工具」(topic_recommender/title_signal/ending_signal/illustrate_decider),但每个 harness step 的 `python -c` 是**signal + dedup 成对调用**。只补 4 个 → 文档会变成「一半 CLI 一半 `python -c`」的杂糅,违背「docs 用真命令」的目标。要真正清掉 `python -c`,必须连带补 dedup 工具。**目标 = SKILL/references/WRITE_AGENT 里 `python -c` 归零**,据此倒推工具集:

| docs `python -c` 出处 | 调用的函数 | 涉及工具(需 CLI) |
|---|---|---|
| Step 1.x rank + 去重 | `rank_aihot_candidates` + `check_event_dedup` | topic_recommender + **event_dedup**(CLI 状态待核) |
| Step 1.5 opening harness | `score_opening_signal` + `check_opening_overlap` | opening_signal + opening_dedup |
| Step 3.3 title harness | `score_title` + `check_title_overlap` | title_signal + title_dedup |
| Step 3.5 ending harness | `score_ending_signal` + `check_ending_overlap` | ending_signal + ending_dedup |
| Step 7.3 出图 | `generate_from_decision` + `write_metadata` | illustrate_decider(`--generate`) |
| Step 2 深搜合并 | `merge_with_websearch` | iti_explore(`--merge-ws`,explore CLI 已有) |

**关键安全事实(survey `a3bf2938386344a47` 实测)**:8 个工具的 `__main__` 全是 `cli_demo()`/`cli_dry_run()`,**无任何测试调用 `__main__`/`cli_demo`** → 可安全把 `__main__` 改 argparse,不破坏现有测试。`opening_dedup` 额外导出 `tokenize/jaccard/...` 基础库给 title/ending dedup 用 —— **不许动这些导出**。

---

## 每工具 CLI 设计(flag 名对齐 W5 docs 已暗示的形态;输入从文件/字符串读)

> 共同原则:① 保留 `cli_demo()`/函数本体不动,只重写 `__main__`(或把 `__main__` 逻辑抽成 `def main(argv=None)` 便于测试)② CLI 默认 **stdout 打印 JSON**(`ensure_ascii=False`),可选 `--out` 写文件 ③ 退出码 0 正常 ④ 不触碰函数签名/业务逻辑(invariant:不改打分/去重算法,反 p-hacking)。

| 工具 | 新 CLI | 行为 |
|---|---|---|
| `topic_recommender.py` | `--pool <iti_pool.json> [--ws <ws.json>] [--out <ranked.json>]` | 读 pool.items(+ws 合并)→ `rank_aihot_candidates` → 打印/写 ranked JSON |
| `event_dedup.py` | `--in <ranked.json> [--days 7] [--include-published] [--current-draft <p>] [--out <chosen.json>]` | 逐条 `check_event_dedup`,输出首个非撞型 chosen + filtered 列表(先核 event_dedup 是否已有 CLI) |
| `title_signal.py` | `--title "..." [--topic-keywords e1 e2] [--body-chars N \| --draft <p>]` | `score_title`;`--draft` 时从 frontmatter 抽 title + 算 body_chars |
| `title_dedup.py` | `--title "..." [--hook-type H] [--draft <self>] [--max-age-days 14] [--max-n-check 10]` | `check_title_overlap`(`--draft` → current_draft_path 防 self-match) |
| `ending_signal.py` | `--draft <md>` | 读全文 → `score_ending_signal` |
| `ending_dedup.py` | `--draft <md> [--max-age-days 30] [--max-n-check 5]` | 读全文 → `check_ending_overlap`(draft 同时作 current_draft_path) |
| `opening_signal.py` | `--trial <txt> \| --draft <md>` | trial 直读;draft 抽 intro(剥 frontmatter,取第一个 `\n## ` 前)→ `score_opening_signal` |
| `opening_dedup.py` | `--trial <txt> \| --draft <md> [--current-draft <p>]` | 同上取 opening → `check_opening_overlap` |
| `illustrate_decider.py` | 把 `__main__` 改 argparse:`--draft <md> [--dry-run]`(默认 dry)+ **`--generate --decision <json> [--slug S]`** | dry = read_article_meta+pick_candidates;generate = `generate_from_decision(dec, OUT_DIR, slug, max_workers=3, retry_failed=True)` + `write_metadata` |
| `iti_explore.py` | 现有 explore CLI + **`--merge-ws <ws.json> --out <facts.json>`** | explore_topic + `merge_with_websearch` 一步落 facts.json |

---

## 改动文件清单 + commit 计划(每文件一 commit,§11)

**阶段 1 — 工具 CLI(test-first,每工具:先写 test → 跑挂 → 加 argparse → 跑过 → 1 commit)**
- C1 topic_recommender + test · C2 event_dedup(先核 CLI 状态)+ test · C3 title_signal + test · C4 title_dedup + test · C5 ending_signal + test · C6 ending_dedup + test · C7 opening_signal + test · C8 opening_dedup + test · C9 illustrate_decider(`--generate`)+ test · C10 iti_explore(`--merge-ws`)+ test
- 测试放 `tools/test_<tool>_cli.py`(或并入现有 test 文件);每个 test 用 tmp fixture(小 draft/json)跑 `main([...])` 断言返回合法 JSON / exit 0。illustrate `--generate` 实 API 不 unit 测,只测 argparse 到达 generate 分支(mock 或 dry 断言)。

**阶段 2 — 回写 docs(python -c → 真 CLI;每文件一 commit + vendor 同步)**
- C11 SKILL.md(骨架 5 处)· C12 stage_01_collect · C13 stage_02_write · C14 stage_04_publish · C15 WRITE_AGENT(v1.8)

**阶段 3 — 记录 supersession + 收尾**
- C16 ARCH_REFACTOR_V1_PLAN.md(W6 行 + 决策 #4 加 supersede 注)+ REFACTOR_PLAN §0/§4.6/§5/§11
- 收尾:verify(全工具 CLI smoke + verify_baseline 零回归 + docs python -c 归零)+ reviewer + Musk → §0 W6 ✅

---

## 验收命令(本 wave 专有)

1. **零回归**:`python -X utf8 scripts/verify_baseline.py` → ALL PASS(新增 ~10 个 CLI test 后 pytest 数应 ≥ 139 + 新增)。
2. **python -c 归零**:`grep -rn 'python -c' SKILL.md references/ WRITE_AGENT.md` → 0(全替成 `python tools/X.py`)。
3. **每工具 CLI smoke**:`python tools/<tool>.py --help` 不崩 + 对 fixture 跑出合法 JSON。
4. **算法零改动**:`git diff` 确认只动 `__main__`/新增 `main()` + argparse,**signal/dedup/rank 打分逻辑一行未改**(reviewer 专项核,反 p-hacking)。
5. **cli_demo 仍在**:每工具 `cli_demo()`/`cli_dry_run()` 函数保留(可被 `--demo` 触发或仍可 import)。

---

## 风险 + 兜底

| 风险 | 兜底 |
|---|---|
| 改 `__main__` 破坏被 import 的基础库(opening_dedup 的 tokenize/jaccard)| 只改 `if __name__=='__main__'` 块,不动模块级函数/常量;survey 已确认 test_stability 只 import 基础库不碰 __main__ |
| 误改打分阈值/逻辑(p-hacking 嫌疑)| 铁律:W6 只加 I/O 层(argparse + 读文件 + 打印),**0 改业务函数**;reviewer 验收 #4 专项 diff |
| `--draft` 抽 frontmatter/intro 的解析与 gate.py/illustrate_decider 既有 parser 不一致 | 复用现有 `read_article_meta` / 既有 frontmatter parser,不另写一套 |
| event_dedup 可能已有 CLI | C2 先核现状,有则只补缺口不重写 |
| illustrate `--generate` 实 API 无法 unit 测 | 只测 argparse 到达 generate 分支 + dry 路径;实跑留 e2e(W10) |
| W6 范围比「4 工具」大(~9)| 已在 scope 段说明:目标是 python -c 归零,据此倒推;非镀金 |

---

## reviewer subagent prompt(全新 session)

> 你是 arch-refactor-v1 **W6 重定义**的独立 reviewer(全新 session)。只读。W6 = ① 给 ~9 个无 CLI 工具加 argparse(test-first)② 把 docs 的 `python -c` 回写成真 CLI ③ 记录「ship.py 编排被 W3 slash 取代」。**W6 不建 Python ship.py**(理由见 spec 顶部)。
>
> 读 `refactor_specs/wave_06_real_clis.md` + `git diff <W5末>..HEAD`。逐条核:
> 1. **业务逻辑 0 改动**(最关键,反 p-hacking):每个工具的 diff 是否**只**动 `__main__`/新增 `main()`/argparse + 读文件 + 打印?signal/dedup/rank 的打分函数、阈值、词典有没有被碰?(碰了 = P0)
> 2. **CLI flag 对得上函数签名**:`--draft` 读全文给 score_ending_signal?`--title`+`--topic-keywords` 给 score_title?`--pool` 读 .items 给 rank_aihot_candidates?`--generate --decision` 到达 generate_from_decision?(对照 tools 源码)
> 3. **docs python -c 归零**:`grep -rn 'python -c' SKILL.md references/ WRITE_AGENT.md` = 0?替换后的 `python tools/X.py` 命令真能跑(flag 对)?
> 4. **cli_demo 保留** + opening_dedup 基础库导出未动?
> 5. **test-first 真做**:每工具有对应 CLI test?test 跑 main([...]) 断言合法输出?
> 6. **Bug 4 防 self-match**:dedup CLI 的 `--draft`/`--current-draft` 正确传 current_draft_path?
> 7. **§8.7 同步**:SKILL/references/WRITE_AGENT/vendor 一致?supersession 在 ARCH + REFACTOR_PLAN 都记了?
> 8. **invariant #4 / 统一语言**:没有建竞争性 ship.py?CLI 是单一职责(signal/dedup 分开)?
>
> binary verdict:**SHIP** / **REVISE**(列 P0)。P0 = 业务逻辑被改 / python -c 未清零 / CLI flag 跑不通 / 破坏现有测试。
