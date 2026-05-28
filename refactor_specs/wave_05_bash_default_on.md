# Wave 5: Python 伪代码 → bash 真命令 + DEFAULT-on opt-out 全文清扫

> 策略出处:`docs/ARCH_REFACTOR_V1_PLAN.md` A4 + 官方 issue #19308
> 执行协议:`REFACTOR_PLAN.md` §2 wave 执行模式 + §11 接续协议
> 状态:🚧 in-progress(2026-05-27 开工)

---

## 物理目的(一句话)

把 fengyun-publish SKILL/references + WRITE_AGENT 宪法里的 **Python 伪代码块**(Claude 当 "reference 不是 command",issue #19308)和**「如果用户没指定 → 跑 X」条件触发**(Claude 挑省事路),全部清扫成**可直接运行的 bash 真命令 / 显式 skill-invoke 步骤 / DEFAULT-on opt-out 措辞**。

---

## ⚠️ 开工前 explorer 实测发现(决定 scope 的关键事实)

explorer agent(`a0e431c417d9614ba`)+ 主线程二次核验 `tools/*.py` 源码,得到精确 CLI 映射。**两个超出 A4 原始假设的事实**:

### 事实 1:~8 个伪代码符号没有可用 CLI

A4 写改造规则时(W1 之前,SKILL.md 还是 1480 行单体)默认「每个伪代码函数都对应一个 CLI」。**实测不成立**:

| 符号 | 工具 | CLI 现状(已核验源码) |
|---|---|---|
| `collect_pool` | iti_collect.py | ✅ 真 argparse:`--hours` `--out` `--no-write` |
| `explore_topic` / `merge_with_websearch` | iti_explore.py | ✅ `explore_topic` 有 CLI(positional slug/title + `--entities` `--main-source-urls`);⛔ `merge_with_websearch` 仅 importable |
| `fengyun_lint` | fengyun_lint.py | ✅ `sys.argv[1]` 单 positional path(无 argparse 但能跑) |
| `critic_vote` | critic_vote.py | ✅ 真 argparse:`--b-verdict` `--c-verdict` `--all-rounds` `--out` |
| `generate_cover_by_template` | generate_cover_by_template.py | ✅ 真 argparse:`--draft`(required)+ 8 可选 |
| `post_fengyun_publish` | post_fengyun_publish.py | ✅ 真 argparse:positional draft + 9 可选 |
| `invocation_log` / `gate` | invocation_log.py / gate.py | ✅ 真 argparse(W4 产物) |
| `read_article_meta` / `pick_candidates` | illustrate_decider.py | 🟡 仅 `<draft> [--dry-run]` positional(raw sys.argv,**无 `--draft` flag**) |
| `rank_aihot_candidates` | topic_recommender.py | ⛔ **只有 `cli_demo()`,无 argparse** |
| `score_opening_signal` | opening_signal.py | ⛔ **只有 `cli_demo()`** |
| `score_title` | title_signal.py | ⛔ **只有 `cli_demo()`** |
| `score_ending_signal` | ending_signal.py | ⛔ **只有 `cli_demo()`** |
| `check_opening_overlap` / `check_title_overlap` / `check_ending_overlap` | *_dedup.py | ⛔ **只有 `cli_demo()`** |
| `generate_from_decision` / `write_metadata` | illustrate_decider.py | ⛔ 仅 importable(CLI 只跑 dry_run) |
| `fengyun_writer_trial` / `invoke_writer_change_title` / `revise_ending_section` | (无工具文件) | ⛔ **是 skill-invoke,不是 bash 命令** |

### 事实 2:SKILL.md 里已有 5 条「假命令」(W1 遗留缺陷)

W1 把 SKILL.md 拆成「干净 bash 骨架」时,写了 5 条**看起来真、实际跑不通**的命令(比伪代码更糟 —— 伪代码 Claude 知道是 reference,假命令 Claude 真跑会 error / 静默跑 demo):

| SKILL.md 行 | 假命令 | 真相 |
|---|---|---|
| L53 | `python tools/topic_recommender.py --pool ...` | topic_recommender 无 argparse,`--pool` 被忽略 → 跑 demo |
| L70 | `python tools/title_signal.py <draft> --entities ...` | title_signal 无 argparse → 跑 demo |
| L71 | `python tools/ending_signal.py <draft>` | ending_signal 无 argparse → 跑 demo |
| L104 | `python tools/illustrate_decider.py --draft <draft>` | 真实是 positional;`--draft` 会被当 `sys.argv[1]` → `Path("--draft")` 读文件崩 |
| L106 | `python tools/illustrate_decider.py --generate` | 无 `--generate` flag,`generate_from_decision` 无 CLI,两个分支都跑 dry_run |

**结论**:SKILL.md 不是「review-only」,是 W5 必改目标。修复假命令属于 W5 charter 核心(「代码全是 bash 真命令」)。

---

## 🔒 W5 scope 决策(主线程拍板,reviewer + Musk 复核)

**W5 = 纯文档清扫,0 行工具代码改动。** 把每条命令改成**当前就能直接运行**的形态:

1. **真 CLI 存在** → 用核验过的真命令(flag 名对齐 explorer 映射)。
2. **仅 importable(无 CLI)** → `python -c "..."` 一行命令,**输入从文件读**(不把长文当 arg 传)。这是真·可运行 bash,解决 #19308(不是 reference 是 command)。
3. **skill-invoke**(writer 试稿/改标题/改末段、huashu/wangxiaobo/content-judge) → 显式「invoke `<skill>` skill」步骤,**不写 bash 也不写伪代码**(对齐 A4 #3:靠 prompt 的硬约束改 hook,skill 调用就老实写成 skill 步骤)。
4. **harness 循环 + critic vote**(本质是 loop + skill-invoke + 打分的编排) → 改成**带 DEFAULT-on 措辞的编号过程**,内部打分步用 `python -c`,改稿步写 skill-invoke。删 ```python 代码块(#19308 触发源)。
5. **条件触发**(2 处 `如果用户没指定 → 跑 ITI`) → `**DEFAULT: 必跑 X**。**Opt-out**:仅当用户消息显式含「主题已定/跳过选题/用 X 主题」时跳过`。

**为什么 doc-only,不在 W5 加 CLI wrapper(给 topic_recommender / title_signal / ending_signal / illustrate_decider 加 `--draft`/`--pool`/`--generate`)**:

- **守 wave charter**:W5 在 §0 定义为「单 agent + verify(跑 dry-run)」的文档清扫,不是「加工具 + 写测试」。改工具代码 = 改 wave 风险画像 + verify 策略,属 scope drift(方法论反对)。
- **Musk W5 预警 ①**(W4 监督员留,§11):「W5 切 bash 时确认这些工具的**调用路径 + stdin 解析不被破坏**」 —— 这是**核验别破坏**,不是新增 argparse。给现有 `cli_demo` __main__ 块加 argparse 有破坏 demo / 改 call path 风险,且要配新测试。
- **invariant #4(0 消费者 = 0 生产)**:CLI wrapper 现在只有「文档消费者」,没有「orchestrator 消费者」—— **W6 才决定 ship.py 是 import 还是 subprocess 调这些工具**。在 W6 定接口前先加 CLI = 可能白建。`python -c` 是当前唯一确定有消费者(/ship subagent + 文档读者)的最小可运行桥。
- **Jobs 敢砍**:不在 doc wave 里 gold-plate 工具。`python -c` 老实可跑就够。

**→ W6 follow-up(写进 §4.5 完工记录 + handoff)**:W6 重写 ship.py 时,顺手给这 4 个工具加 `--draft`/`--pool`/`--generate` 真 CLI(带测试),然后文档里的 `python -c` 一行可简化成 `python tools/X.py --draft Y`。W5 先用 `python -c` 让全链路**真能跑 + 老实**。

---

## 改动文件清单(精确到行号)

> 单写者(主线程)。每文件一 commit(§11 铁律)。改 skill 文件后同步 `vendor/skills/fengyun-publish/`(§8.6),并入同一 commit。WRITE_AGENT.md 在 repo 根,直接 git 跟踪,无 vendor 镜像。

### C1 · `SKILL.md`(+ vendor 镜像)— 修 5 条假命令

| 行 | 改前(假) | 改后(真) |
|---|---|---|
| L53 | `python tools/topic_recommender.py --pool ...` | `python -c` 调 `rank_aihot_candidates`(读 iti_pool.json) |
| L70 | `python tools/title_signal.py <draft> --entities ...` | `python -c` 调 `score_title` |
| L71 | `python tools/ending_signal.py <draft>` | `python -c` 调 `score_ending_signal`(读 draft) |
| L104 | `python tools/illustrate_decider.py --draft <draft>` | `python tools/illustrate_decider.py output/drafts/<slug>-v0.md --dry-run` |
| L106 | `python tools/illustrate_decider.py --generate` | `python -c` 调 `generate_from_decision` + `write_metadata`(读 image_decision.json) |

### C2 · `references/stage_01_collect.md`(+ vendor)
- L19 条件触发 → DEFAULT-on opt-out
- L21-65 ```python(collect_pool + rank + event_dedup + WebSearch) → bash(iti_collect 真 CLI)+ `python -c`(rank_aihot_candidates / check_event_dedup)+ WebSearch 编号步骤
- L80 条件触发(`如果用户没指定 → Step 1.0`) → DEFAULT-on
- L119-170 ```python opening harness loop → 编号过程(skill-invoke 试稿 + `python -c` 打分/去重 + DEFAULT 上限 3)
- L251-281 ```python(explore_topic + merge_with_websearch + WebSearch) → bash(iti_explore 真 CLI)+ `python -c`(merge_with_websearch)+ WebSearch 编号步骤

### C3 · `references/stage_02_write.md`(+ vendor)
- L50-97 ```python title harness loop → 编号过程(`python -c` score_title/check_title_overlap + skill-invoke 改标题 + DEFAULT 上限 3)
- L144-192 ```python ending harness loop → 编号过程(`python -c` score_ending_signal/check_ending_overlap + skill-invoke 改末段 + DEFAULT 上限 3)

### C4 · `references/stage_04_publish.md`(+ vendor)
- L148-153 ```python pick_candidates → bash `python tools/illustrate_decider.py <draft> --dry-run`
- L160-164 ```python cover_anchor 读 sidecar → bash(`cat`/读文件说明,这是读已存在文件不是工具调用)
- L181-185 ```python generate_from_decision + write_metadata → `python -c`(读 image_decision.json)

### C5 · `WRITE_AGENT.md`(直接,无 vendor)— 9 个 ```python 块
| 块行 | Step | 改后 |
|---|---|---|
| L320-331 | 1.x rank+event_dedup | `python -c`(rank_aihot_candidates)+ `python -c`(check_event_dedup)/ 编号 |
| L406-416 | 2 explore_topic | bash(L419 已有真 CLI;删冗余 python 块,正文指向真 CLI)+ `python -c`(merge) |
| L484-499 | 3.3 title harness | 编号过程(同 C3) |
| L525-536 | 3.5 ending harness | 编号过程(同 C3) |
| L554-559 | 4 lint | bash `python tools/fengyun_lint.py <draft>` |
| L627-637 | 6 critic vote | 编号过程(skill-invoke B/C + bash critic_vote.py;本块多为注释,清成步骤) |
| L709-713 | 7.1 pick_candidates | bash `illustrate_decider.py <draft> --dry-run` |
| L755-759 | 7.2 cover_anchor | bash(读 sidecar 说明) |
| L777-783 | 7.3 generate | `python -c`(generate_from_decision + write_metadata) |

### 不在 W5 scope(已核验)
- `references/stage_03_verify.md`(0 ```python,0 条件触发)— review-only
- `references/failure_modes.md` / `frontmatter_checklist.md`(0 ```python)— review-only
- `SKILL.md.pre-w1-bak`(W1 备份,Claude 不加载)— 不动
- 其它 skill(huashu/content-judge/fengyun-writer)— 是被 invoke 的 reviewer/writer,不是编排 SOP,不在 #19308 scope
- 工具 `*.py` 源码 — 0 改动(见 scope 决策)

---

## 改前 vs 改后(每种 pattern 一个样例)

### Pattern A · importable-only → `python -c`(SKILL.md L71 ending_signal)
```diff
- - `python tools/ending_signal.py <draft>`
+ - 结尾打分(ending_signal 无 CLI,从 draft 文件读):
+   `python -c "import sys,json; sys.path.insert(0,'tools'); from ending_signal import score_ending_signal; from pathlib import Path; print(json.dumps(score_ending_signal(Path(r'output/drafts/<slug>-v0.md').read_text(encoding='utf-8')), ensure_ascii=False))"`
```

### Pattern B · 修假 flag → 真 positional CLI(SKILL.md L104)
```diff
- - `python tools/illustrate_decider.py --draft <draft>` Step 7.1 函数预筛候选位置
+ - `python tools/illustrate_decider.py output/drafts/<slug>-v0.md --dry-run` — Step 7.1 函数预筛候选位置(positional path + --dry-run)
```

### Pattern C · 伪代码 loop → DEFAULT-on 编号过程(stage_02 title harness)
```diff
- ```python
- from tools.title_signal import score_title
- from tools.title_dedup import check_title_overlap
- for attempt in range(3):
-     signal = score_title(title, topic_keywords=entities, body_chars=len(...))
-     dedup = check_title_overlap(title, ..., current_draft_path=draft_path)
-     if pass_signal and pass_dedup: break
-     new_title = invoke_writer_change_title(...)
- ```
+ **DEFAULT:跑标题 harness(上限 3 轮,不达标用最后一版)**。每轮:
+ 1. 打分:`python -c "...; from title_signal import score_title; print(json.dumps(score_title(TITLE, topic_keywords=ENTITIES, body_chars=N), ensure_ascii=False))"`
+ 2. 去重:`python -c "...; from title_dedup import check_title_overlap; print(json.dumps(check_title_overlap(TITLE, hook_type=HT, current_draft_path='output/drafts/<slug>-v0.md'), ensure_ascii=False))"`(必传 current_draft_path 防 self-match)
+ 3. signal verdict=pass 且 dedup 不撞型 → break
+ 4. 否则 invoke `fengyun-writer` skill(改标题模式,只改 frontmatter title 带 feedback),回填后回 1
+ 5. 到第 3 轮仍不过 → 用最后一版(不阻塞)
```

### Pattern D · 条件触发 → DEFAULT-on opt-out(stage_01 L19)
```diff
- 如果用户没指定具体事件,只给了「ship 一篇」「随便选个热点」这种泛指 → 跑 ITI 数据驱动选题:
+ **DEFAULT:必跑 ITI 数据驱动选题**(I-1 广搜 → T 排序 → 去重)。
+ **Opt-out**:仅当用户消息**显式**含「主题已定」/「跳过选题」/「用 X 主题」时,跳过本步直接用指定主题。
```

### Pattern E · skill-invoke(stage_01 opening harness 写稿步)
```diff
- if attempt == 0:
-     trial = fengyun_writer_trial(north_star, core_event)
- else:
-     trial = fengyun_writer_trial(north_star, core_event, avoid_feedback=prev_feedback)
+ - 第 1 次:invoke `fengyun-writer` skill 试稿模式(出 200 字开头,不出完整稿)
+ - 第 2/3 次:同样 invoke `fengyun-writer`,prompt 注入上轮 redo_feedback(让它避开上次问题)
```

---

## 验收命令(本 wave 专有)

> verify subagent 静态轨优先;sandbox 拒 Bash 时主线程动态轨兜底(§8.5.2),commit message 诚实标注。

1. **零回归**:`python -X utf8 scripts/verify_baseline.py` → **121 passed / 0 deselected**(W5 不碰代码/测试,必须原样过)。
2. **伪代码清零**:`grep -rc '```python'` 对 SKILL.md + 3 references + WRITE_AGENT → **全 0**(`.pre-w1-bak` 除外)。
3. **假 flag 清零**:`grep -n '\-\-pool\|\-\-generate\|title_signal.py <\|ending_signal.py <\|topic_recommender.py \-\-' SKILL.md` → **0 命中**。
4. **条件触发清零**:`grep -rn '如果用户.*→\|如果用户没指定' references/` → **0 命中**(或全部 superseded 标注)。
5. **`python -c` 引用的函数真存在**(import-smoke):
   ```bash
   python -c "import sys; sys.path.insert(0,'tools'); from title_signal import score_title; from ending_signal import score_ending_signal; from opening_signal import score_opening_signal; from topic_recommender import rank_aihot_candidates; from title_dedup import check_title_overlap; from ending_dedup import check_ending_overlap; from opening_dedup import check_opening_overlap; from iti_explore import merge_with_websearch; from illustrate_decider import generate_from_decision, write_metadata, pick_candidates, read_article_meta; print('ALL IMPORTS OK')"
   ```
6. **真 CLI dry-run**:`python tools/iti_collect.py --help`(argparse 工具)+ `python tools/illustrate_decider.py output/drafts/<任一已存在draft>.md --dry-run` 不崩。
7. **vendor 镜像同步**:`git diff --stat` 确认每个改的 skill 文件 vendor 副本一并变更。

---

## 风险 + 兜底(本 wave 专有)

| 风险 | 兜底 |
|---|---|
| `python -c` 单行在 Windows PowerShell 引号转义炸 | 文档统一用 bash 风格(项目既有 bash 块惯例);`python -c` 内字符串用单引号包路径,JSON dumps `ensure_ascii=False`;真跑由 /ship subagent 在 Bash 工具里执行 |
| 改 harness loop 编号过程时漏掉某个 Bug 4 注释(current_draft_path 防 self-match) | 每个 dedup `python -c` 显式带 `current_draft_path`;reviewer 专项查 |
| WRITE_AGENT L406 explore 块删掉后,正文逻辑断 | L419 已有真 CLI 块,删的是冗余 python 镜像,正文指向真 CLI;不删 CLI 块 |
| 漏改某条 SKILL.md 假命令,W5「完成」但命令仍跑不通 | 验收 #3 grep 假 flag 清零卡死 |
| scope 决策(doc-only 不加 CLI)被 reviewer/Musk 判为偷懒 | 决策写明出处(charter + Musk 预警 ① + invariant #4 + W6 归属);若判 P1 → 记 W6 follow-up,不卡 W5 commit |
| `python -c` 比真 CLI 丑,损 SKILL.md 可读性 | 接受为过渡态;§4.5 + handoff 明确 W6 加真 CLI 后简化 |

---

## reviewer subagent prompt(全新 session 审稿用)

> 你是 arch-refactor-v1 W5 的独立 reviewer(全新 session,没参与改稿,防 self-bias)。只读不改。工作目录 `D:\Dev\ai-wechat-pipeline`,分支 `arch-refactor-v1`。
>
> **背景**:W5 把 fengyun-publish SKILL/references + WRITE_AGENT 的 Python 伪代码 + 条件触发清扫成可运行 bash / `python -c` / skill-invoke 步骤 / DEFAULT-on opt-out。**W5 是 doc-only,0 行工具代码改动**(理由见 spec scope 决策)。
>
> 读 `refactor_specs/wave_05_bash_default_on.md` + `git diff backup-pre-refactor-20260526..HEAD -- WRITE_AGENT.md vendor/skills/`(或 `git log -p` W5 各 commit),逐条核:
> 1. **伪代码清零**:SKILL.md + stage_01/02/04 + WRITE_AGENT 还有没有 ```python 块?(`.pre-w1-bak` 不算)
> 2. **命令真能跑**:每条 `python tools/X.py ...` 的 flag 是否对得上工具真实 argparse/sys.argv?(重点抽查 topic_recommender/title_signal/ending_signal/illustrate_decider —— 它们**无 argparse**,doc 里应是 `python -c` 或正确 positional,不能再出现 `--pool`/`--entities`/`--draft`/`--generate` 假 flag)
> 3. **`python -c` 引用的函数真存在**:跑 spec 验收 #5 的 import-smoke。
> 4. **skill-invoke 老实**:writer 试稿/改标题/改末段、huashu/wangxiaobo/content-judge 是否写成「invoke skill」步骤,而非伪 bash?
> 5. **DEFAULT-on**:2 处条件触发是否改成「DEFAULT 必跑 + 显式 opt-out」?有没有残留「如果用户没指定 → 」?
> 6. **Bug 4 防 self-match**:title/ending/opening dedup 的 `python -c` 是否都带 `current_draft_path`?
> 7. **vendor 镜像**:每个改的 skill 文件 vendor 副本是否同步?
> 8. **§8.7 同步矩阵**:改 SKILL/references 是否漏了下游(本 wave 不动 critic/lint 逻辑,主要核 WRITE_AGENT 宪法与 SKILL 一致)?
> 9. **scope 决策合理性**:doc-only 不加 CLI 是合规决策还是偷懒?(若认为该加 CLI,判 P1 记 W6,不要求 W5 当场加)
>
> 出 binary verdict:**ship**(可 commit 收尾)/ **revise**(列 P0/P1)。P0 = 假命令残留 / 伪代码残留 / import-smoke 失败 / 回归。
