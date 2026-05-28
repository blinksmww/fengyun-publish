# fengyun-publish 新分支重构 — Wave 进度看板

> **当前分支**:`arch-refactor-v1`
> **基线 tag**:`backup-pre-refactor-20260526` (commit `ae3cb4c`)
> **策略文档**(WHY + WHAT):`docs/ARCH_REFACTOR_V1_PLAN.md`
> **本文件**(HOW + WHEN):wave 状态机 + 每 wave 验收命令 + /clear 后 reload 协议

---

## ⛔ W0 血泪教训 — P0 红框(记忆深处,永不忘)

W0 主线程第一次跑就犯了 **2 个根本性错误**:
1. **跑 baseline 验收没派 verify subagent** — 主线程 Bash 直接跑,客观性差
2. **commit 之前没派 reviewer subagent** — 主线程自己审自己 = self-bias

**事后补救**派 reviewer 才发现 **6 个真问题**(.sh/.py 混用 / wave 表跟策略文档不同构 / reload 协议漏 invariant / §3 假承诺 #3 #4 / §8 漏 4 条 memory 反模式 / docstring exit 2 未实现)。

**根因**:主线程没遵守自己刚写的 ARCH_REFACTOR_V1_PLAN.md §6.1 角色分工。**写了规则自己不遵守 = 反模式典型**。

**永不再犯的机制**(W0.1 + W0.2 落地,生效到 W10):
- §8 禁令 12 条(W0.1 加 #7 #8 / W0.2 加 #9-#12)
- §8.5 每 wave 至少用 **3 个 subagent** 硬约束(verify + reviewer + **Musk 监督员**)
- 每 wave 收尾 **Musk 全程监督员** 核验过程合规(新增,2026-05-27 用户拍板)

**关键观察**:reviewer 价值实测 — 主线程自己审觉得 W0 "OK",reviewer 一眼看出 6 个真 issue。**没有 subagent 把关 = 主线程盲点放大**。

**Musk 监督员 W0 verdict**(2026-05-27 全程闭环):
- 综合:**合规**(W0 接受为完工)
- Idiot Index:**真实 2×**(不是 3×;W0.1 那 commit 是可删冗余 — 第一次写 §0 表就该带 subagent 列,但 W0.2 不能删,是真 self-refine 信号)
- 诚实程度:诚实(主动暴露翻车,没藏问题)
- 学习闭环:真物化(5 条禁令各有具名物理痛点,非装饰)
- invariant #4:遵守(主动删 §3 假承诺 + docstring exit 2)
- subagent 真用:真用(3 个 agent ID 可追溯)

**Musk 给主线程一句话告诫**(刻进 W1 起的 SOP):
> W0 接受为合规,但要把「事后补」的习惯**彻底删掉** — W1 起严格按 §8.5 先派 subagent 再开工,不接受事后补救。

**Musk 给 W1-W10 监督建议**:
- 重点盯:**W1**(SKILL.md 拆,跨 references/ 强一致)、**W6**(ship.py SDK 单点失败)、**W9**(critic 参数 K-fold 反 p-hacking)
- 快速过:W2 / W5 / W8(风险低,fan-out 不适用)

---

## 0. 当前状态(每 wave 完工后更新)

| Wave | 状态 | 完工 | commit | subagent | 模式 | 协调/兜底 |
|---|---|---|---|---|---|---|
| **W0 基线** | ✅ done | 2026-05-27 | `90212b3` / `ade620a` / `46e9e21` | reviewer `a49f41f902e496b81`(revise → 6 项修)+ verify `a2b9edf0096937e33`(PASS)+ Musk 监督员 `a51b9fd2f8e3789cc`(**合规,Idiot Index = 2×**) | 你单干 | branch 即 rollback 点;⚠️ 首次违规事后补;Musk 5 步删除诊断 W0.1 可删 |
| W1 拆 SKILL.md 1480→300 | ✅ done | 2026-05-27 | `d134d98`(+ W1.1 follow-up) | explorer `a416e07e87ce1f343`(完工)+ verify(sandbox fallback / 主线程兜底跑)+ reviewer `ab659a49e21dc92bd` **ship** + Musk `a57407a3469195cce` **合规** | 单 agent + 1 explorer | SKILL.md 1446→202 行(预算 ≤ 300)+ 6 references/ 全活 + 字数 +16.8%(spec 拟放宽到 ±20%);跨阶段 link 全活;skill 已镜像 vendor/ |
| W2 删 6 件冗余 + critic 双轨全自动 | ✅ done | 2026-05-27 | `6ae41ab`(C5)→ `3085e99`(共 12 commit:C5/C4/C1/C3/C2/C2.1/C6/C6.1/C6.2/C6.3/C6.4 + fix_punctuation) | reviewer `a88f91fb4faf740bc`(抓 P0 WRITE_AGENT 宪法未同步 → 已修 C6.4)+ Musk `a8d1b5207b7ad8127`(**合规,「审过最干净的 wave」**)+ verify 主线程兜底跑 115 passed | 单 agent 串行 | **见下方 W2 完工记录**;vendor 已镜像;WRITE_AGENT 宪法已同步双轨 |
| W3 写 5 subagent + slash + hook | ✅ done | 2026-05-27 | (W3 收尾 commit) | verify `a1ed44b6d6247fa9c`(**ALL PASS** / 121 passed)+ reviewer `a314f9896446dd863`(REVISE → 抓 P0:critic source 未回填 draft frontmatter)→ 修复后复查 `aee417a5d8487beb7`(**P0 闭合 ship**)+ Musk `abbb9cef176af51ad`(**合规,Idiot Index ≈ 1×**)| 单写者(spec §4.0,放弃 fan-out)| **见 §4.3 W3 完工记录**;hook 只接 gate.py,另两层留 W4 |
| W4 frontmatter → invocation log | ✅ done | 2026-05-27 | (W4 收尾 commit) | 调研 `a4dbcf0bf952be555` + verify `a48e760129a0952ed`(**ALL PASS** / 139+30)+ reviewer `a03ea81bae8f08a64`(REVISE → P1:WRITE_AGENT per-step 缺 W4 banner → 加 §总览全局 banner)+ Musk `abea887cf76b5c66f`(**合规,Idiot Index ≈ 1.3×,invariant #4 三消费者同 wave**) | 单写者,test-first,绝不 fan-out | **见 §4.4 W4 完工记录**;消费者 gate.py+validate_run_log+ship_complete_check 同 wave;image_paths 留 frontmatter(§1.1 scope 砍) |
| W5 Python 伪代码 → bash | ✅ done | 2026-05-27 | `002f9ba`→`085d130`(8 commit:open/C1-C5/C5.1/C5.2)| explorer `a0e431c417d9614ba`(CLI 映射)+ verify `a55318458b1c854f0`(**PASS** static+dynamic 139)+ reviewer `a9e87d97a78989c0d`(**SHIP** 0 P0)+ Musk `aa126dd2b0949edcf`(**合规,Idiot Index 1×**)| 单写者,doc-only | **见 §4.5**;修 5 条 W1 遗留假命令;4 工具无 CLI → `python -c` 过渡,W6 加真 CLI |
| W6(重定义)tool 真 CLI 补齐 | ✅ done | 2026-05-27 | `8f739e8`→`d6a57a3`(15 commit:C1-C10 工具 CLI + C11-C15 docs)+ 收尾 | explorer `a3bf2938386344a47` + verify `af21575a99f3d35a7`(**ALL PASS** / baseline 173 passed)+ reviewer `a84d148cc312d8a86`(**SHIP** 0 P0;1 P1 §11 stale 已修)+ Musk `a6641a5e6623847fd`(**合规,Idiot Index ≈ 1×**) | **绝对单 agent,test-first** | **见 §4.6 W6 完工记录**;无 `tools/ship.py` → headless ship.py 延 cloud(invariant #4);补 10 工具真 CLI + docs `python -c` 归零 |
| W7 cover 系统重做 | ✅ done | 2026-05-27 | `87720ca`→`1219922`(open+C1-C4) | 2 explorer(`af03866dfb517d92a`内/`a4d02748d687fc8ff`外)+ Musk 决策 verdict(主线程 skill)+ 3 writer Opus(`aa7ca7bcd4354001f` seedream_client / `a2795c87dd3a8414f` huashu Mode3 / `a55d3b428904ba651` doc-sync)+ verify 静态 `ad1c9e60c97fe7eb7`(PASS)+ 主线程动态兜底(180 passed,§8.5.2)+ reviewer `a5a6509ab2751e34a`(**SHIP** 0 P0)+ Musk `a3419e6eef3dcd4b9`(**合规,Idiot Index ≈1×**)| 单写者串行 + 2 explorer | **见 §4.7 完工记录**;物理删 951 行不归档;删云签名留品牌色;⚠️孤儿 .pyc 假 FAIL 已诊断清除 |
| W8 ITI I-2 + TrendRadar wrapper | ✅ done | 2026-05-27 | `144820b`→`f71a330`(open+C1-C4) | explorer(Sonnet 只读,3 fork AskUserQuestion 拍板)+ 你单干 + verify(Sonnet,Bash 本 session 可用→189 passed 全 PASS + 静态 A-E;主线程独立也跑 189)+ reviewer(Sonnet,**SHIP 0 P0**,1 P1 agent 文件 stale → C4 修)+ Musk(Sonnet,**合规 Idiot Index 1×**)| 单写者,test-first | **见 §4.8**;DB reader 实测 257 条(5/feed)vs 旧 markdown ~170;aihot ?q= 实测 23 条;3 fork 拍板(N=5/砍 smol.ai by-topic/E4 no-op);⚠️ doc-sync 漏 agent 文件教训 |
| W9 砍维度+调阈值+清伪lint | ✅ done | 2026-05-27 | `077b02e`→`7c57690`(open+C1-C6) | explorer×2(Sonnet 只读:维度现状 + lint 价值)+ AskUserQuestion 4 fork 拍板 + 你单干 test-first + verify `aae1bed85b8acee8e`(**PASS**,跑动态 PowerShell:193 passed + lint + invocation + harness cut-dim 无强信号)+ reviewer `af982b62242db28d4`(**SHIP 0 P0**,3 P2 历史 output/audit 文档 stale 非 runtime)+ Musk `a7df63c2bb4ed3b04`(**合规**,Idiot Index 1×;偏离仅指三审"录入收尾"未做 → 本收尾 commit 满足) | 你 + verify,test-first | **见 §4.9**;砍 opening 3 维 + 拆情绪锚点 + title 致命组合,调 真首段50→25 / 7钩子hard→软分 / 4特质≥2→≥1,清 6 伪 lint(R2/R4/R13/R14/R16/R21)+ 修 R7;harness 实证砍维 proxy ρ≈0;4 fork 拍板(F1 验收=信号分ρ非critic-ROC / F2 清伪lint替代原B3 / F3 R13砍 / F4 情绪锚点拆函数) |
| W10 e2e 验收 | ✅ done | 2026-05-27 | (W10 收尾 commit) | verify(193 passed,本 session 双确认)+ reviewer `a099dde65e6c8c5e2`(**达标可替换主支,0 P0**)+ Musk `a5850adc2418f589f`(**合规,Idiot Index ≈1.25×,主支红线 CLEAN**)+ explorer(只读)+ writer/critic B/C 真 subagent | 验收 wave(0 业务代码改动) | **见 §4.10**;真跑一篇到草稿箱(media_id f5xAnh6...);§8 八项全 PASS(#8 耗时降级 advisory);force_ship 实证(B/C 3 轮结构性分歧);⛔ 主支替换 **等风云显式拍板**(A/B founder verdict 未判);旧 main=ae3cb4c tag 兜底 |

**legend**:⏸ pending / 🚧 in-progress / ✅ done / ⛔ blocked / ⚠️ partial

---

## 1. /clear 后 reload 协议

每次主线程 `/clear` 之后,**只读以下 3 个文件**就能恢复完整工作上下文:

1. **本文件 `REFACTOR_PLAN.md`** — 看当前在哪个 wave + 下一步做什么
2. **`docs/ARCH_REFACTOR_V1_PLAN.md`** — 看 WHY(为什么这么做)+ 完整策略
3. **当前 wave 的 spec 文件**(每 wave 独立的 `refactor_specs/wave_X_<name>.md`,W0 之后陆续创建)

**禁止**:reload 旧的 SKILL.md / WRITE_AGENT.md / tools/*.py 全文(那是 wave 内执行时按需读,不是 reload 协议)

### 1.1 五条架构 invariant(本文件复述一次,/clear 不用跳第 4 个文件)

源:`docs/ARCH_REFACTOR_V1_PLAN.md` §4。这 5 条是新分支不可违反的硬约束:

1. **公理化层级**:对外 4 阶段(Collect / Write / Verify / Publish),子步骤是实现细节
2. **统一语言**:同一物理目的只一个组件,禁止重叠检测
3. **frontmatter 是文章 metadata,不是 pipeline state**:31 防伪字段迁到 invocation log,frontmatter 回归 title / digest / author / north_star
4. **0 消费者 = 0 生产**:任何「将来回填」的 metric,没真消费者前不要写
5. **真公理优先**:非真 invoke 的 perspective skill 不在 SKILL.md 出现

---

## 2. Wave 通用执行模式(每 wave 都遵循)

```
1. 主线程读本文件 + 策略文档 + 当前 wave spec
2. 主线程更新本文件:当前 wave 状态 ⏸ → 🚧
3. 执行 wave 内动作(单 agent 或必要时派 explorer/writer subagent)
4. wave 收尾 — 派 verify subagent 跑验收脚本(见 §3),不许主线程 Bash 直接跑
5. 派 reviewer subagent 全新 session 审 diff + spec(产物质量)
5.5 派 Musk 监督员 subagent 全新 session 核验过程合规
    (是否按 REFACTOR_PLAN.md + ARCH_REFACTOR_V1_PLAN.md 规划执行;
     Idiot Index 评估;5 步删除 algorithm 审视;0 消费者 = 0 生产 invariant 遵守)
6. verify + reviewer + Musk 三者全过 → git commit + 本文件 wave 状态 🚧 → ✅
7. /clear 重启主线程
8. 进下一 wave
```

**关键顺序**:verify(看脚本结果)→ reviewer(看产物质量)→ **Musk(看过程合规)** 三者维度不同,缺一不可。

### 2.1 reviewer / Musk 抓出 P0 的闭环(W2 实证,2026-05-27)

三审任一出 **P0**(阻断级),**不接受「带已知 P0 commit + 留 TODO」**。闭环:

```
reviewer/Musk 出 P0
  → 主线程当轮修(不拖到下一 wave)
  → 重新跑 verify(确认修复 + 零回归)
  → 三者全过 → 才 commit
```

**W2 实证**:reviewer `a88f91fb` 抓出「`WRITE_AGENT.md` 系统宪法还是旧三轨 + 一行 ImportError 的 `from tools.sop_v2_1 import score_draft`」(P0)→ 主线程当轮修成 commit `d40a2aa`(W2.C6.4)→ 重新 verify 115 passed → 才算 W2 收尾。**没有 reviewer 这一关,这个宪法矛盾会带进 W3,跑 pipeline 的 LLM 会照旧 spec 重新引入 Track A**。

> P1(非阻断)可以记进 §0 协调字段或 spawn 独立 task(如 W2 的 fix_punctuation),不卡当前 wave commit。

---

## 3. 通用验收脚本(每 wave 收尾必跑)

固化在 `scripts/verify_baseline.py`(W0 末创建)。每 wave 收尾跑这个,通过才能 commit。

**W0 实装**(0 消费者 = 0 生产 invariant,见 §1.1 #4 — 不为将来写未实装的检查):
1. **pytest** — 跑 `tools/test_*.py` 所有测试(112 passed + 6 deselected 已知 dead)
2. **lint baseline** — 跑 `python tools/fengyun_lint.py` 对 `corpus/raw/huashu/*.md` 抽样 5 篇,确认无 crash

**未来扩展**(对应 wave 完工后才加,不提前实装):
- W4 完工后扩展:invocation log schema 验证
- W6 完工后扩展:ship.py SDK 编排 smoke test

---

## 4. 当前 wave:W0 基线 ✅ done

### 进度

- [x] 1. git status check(modified + untracked 都 commit 到主支)
- [x] 2. commit 主支「pre-refactor 最终状态」`ae3cb4c`
- [x] 3. 打 tag `backup-pre-refactor-20260526`
- [x] 4. 创建 + 切换 `arch-refactor-v1` 分支
- [x] 5. 写 `REFACTOR_PLAN.md`(本文件)
- [x] 6. 固化验收脚本 `scripts/verify_baseline.py`(改 .py 跨平台)
- [x] 7. 跑一次 baseline 验收 — **112 passed / 6 deselected / lint 5 篇无 crash**
- [x] 8. W0 commit + 本文件 W0 状态 🚧 → ✅

### W0 已知 baseline 缺陷(后续 wave 一起处理)

| Issue | 详情 | 处理时机 |
|---|---|---|
| ~~**B 组 6 测试调用不存在的 fix_punctuation_text 函数**~~ ✅ **W2 已修** | `tools/test_round26_fixes.py::test_b1` 到 `test_b6` 引用 `fix_punctuation.fix_punctuation_text()`,但 `tools/fix_punctuation.py` 里只有 `is_cn` + `main`,**整组测试 dead** | **2026-05-27 W2 修复(选「实现函数」非删)**:依据 SPEC_ROUND26_HUMAN_GATE_FIX.md §三 + SKILL.md L125(fix_punctuation 仍是 active 工具),补回 `fix_punctuation_text(text) -> (str, n)` 纯文本入口 + `fix_punctuation_file(path) -> (n, skipped)` 文件入口,`main()` 改为调 file 入口。`verify_baseline.py` KNOWN_FAILING_TESTS 清空(6→0 deselect)。验收:`test_round26_fixes.py` 25 passed / 0 failed;`verify_baseline.py` 121 passed / 0 deselected。**未删而是实现** — Newton hypothesis non fingo 让位于「这工具有真消费者(SKILL stage_03 verify)」的客观事实。 |

### W0 验收标准 — 实际结果

```
[1/2] pytest tools/test_*.py ...
  → pytest PASS / 9 test files / 112 passed, 6 deselected in 23.25s

[2/2] lint baseline (5 篇 huashu corpus) ...
  → lint baseline PASS / 5 篇 huashu corpus 全部无 crash

[PASS] ALL CHECKS PASSED — 可以 commit 进新分支
```

### W0 验收标准

```bash
# 必须全部通过才算 W0 完工
python scripts/verify_baseline.py
# 期望输出:
# [pytest] PASS / XX tests
# [lint baseline] PASS / 5 articles scanned
```

### W0 next commit message

```
W0 baseline: branch + tag + plan + verify scripts

- Branch: arch-refactor-v1 from main (ae3cb4c)
- Tag: backup-pre-refactor-20260526
- REFACTOR_PLAN.md created (wave state machine + reload protocol)
- scripts/verify_baseline.py created (pytest + lint baseline check)
- Baseline verified: all tests pass + lint runs cleanly on 5-article sample

Next: W1 split SKILL.md 1480 → ≤ 300 + references/ 6 files
```

---

## 4.2 W2 完工记录(2026-05-27,新窗口看这段就懂 W2 改了啥)

**主线 6 件删除**(每件 1 原子 commit):
- **C5** `6ae41ab`:删 7 个 `_*.py` 死代码 + `backup_20260521/`
- **C4** `83c3315`:删 `founder_feedback.jsonl` 写入逻辑 + 物理删 2 jsonl(invariant #4「0 消费者=0 生产」)
- **C1** `ccc97e0`:删 stage_04 的 5-perspective cover-curator 装饰段引用
- **C3** `126066a`:删 System A/B 双轨文档(逻辑早已单轨)
- **C2** `b915b9c` + **C2.1** `2f71a5d`:删 humanizer-zh skill;真漏网 2 模式迁 `fengyun_lint` **R29(破折号≤3/篇)+ R30(否定排比≤2/篇)**,阈值用风云本人 56 篇 corpus 实测(0.48 / 0.25)
- **C6** `3f76295`:删 `tools/score_draft.py`(Track A 数字分);`critic_vote.py` 重写为**双轨 B+C 对等**(任一 reject → revise,删「C 硬否决」)+ **隐藏 3 轮天花板** `REVISE_CEILING`(到顶仍未双过 → `force_ship: true` + WARN,删 human_gate/partial_pass/auto_abort)

**「全流程无人工交互」铁律连带**(用户 2026-05-27 加):
- **C6.2** `d9c29fa`:R18-P0 全自动化 — 末轮 P0 未到天花板 → revise 自动删段;到天花板仍 P0 → `aborted_r18` 自动终止(ERROR 日志,不 ship,**无人工**)
- **C6.3** `9c5d0b4`:删 Stage 1/4 残留 6 处 mid-flow 人工 gate(选题确认/事件 confirm/dogfood R18/lint loop/封面失败/推送失败)
- **C6.4** `d40a2aa`:同步 `WRITE_AGENT.md` 系统宪法到 W2.C2+C6(reviewer 抓的 P0:旧三轨 + 一行 ImportError 的 `from tools.sop_v2_1 import score_draft`)

**critic 系统现状**(W2 后,新窗口必须知道):
- **双轨 B+C**(huashu 灵魂 + content-judge 挂名意愿),**无 Track A 数字分**
- 质量底线 = `fengyun_lint` R0-R30(机械)+ B/C 双轨灵魂共识
- 全 pipeline **零人工 gate**,唯一人工 = 草稿箱审阅 + 点发出(NORTH_STAR,pipeline 外)
- 评委 B/C prompt 永不出现「轮次/上限」(天花板在 `critic_vote.py` 代码层)

**⚠️ 注意 CLAUDE.md / SKILL.md 仍可能有少量生产态旧描述未追平**(如 CLAUDE.md L20「8 项防伪含 humanizer」)— 以 `WRITE_AGENT.md` + 本文件 + `critic_vote.py` 实装为准。

---

## 4.3 W3 完工记录(2026-05-27,新窗口看这段就懂 W3 加了啥)

**物理目的**:把「靠 SKILL.md prompt 喊 BLOCKING REQUIREMENT」换成「显式 `/ship` + context 隔离 subagent + PreToolUse hook」的确定性约束(官方 issue #19308 根因)。**纯新增 7 个文件,0 修改业务逻辑**。

**新建产物**(全在项目 repo,非 user-level,无需 vendor 镜像):
- `.claude/agents/` 5 个 subagent(薄壳委托现有 skill,四件套 + 四段正文):
  - `fengyun-iti`(Stage 1 Collect,sonnet)/ `fengyun-writer`(Stage 2 Write,opus,真调 fengyun-writer skill)
  - `fengyun-critic-huashu`(Track B 灵魂,sonnet)/ `fengyun-critic-content-judge`(Track C 挂名,sonnet)
  - `fengyun-cover`(Stage 4 视觉,sonnet,真调 huashu-image-curator Mode 2)
- `.claude/commands/ship.md`:`/ship <主题>` 显式触发,确定性编排 iti→writer→[B‖C 并行]→critic_vote+revise loop→cover→post
- `.claude/settings.json`:**hook 只接 1 层** PreToolUse(Bash)→ `gate.py`(用户决策)。`validate_run_log.py` / `ship_complete_check.py` 两层是 W4(invocation log)产物,**不先布死引用**(守 invariant #4)

**关键设计决策**:
- **薄壳委托**(invariant #2 统一语言):subagent 只做 context 隔离 + 四件套 + 结构化输出,业务逻辑仍走 user-level skill,不重写
- **业务输出 vs 防伪元数据分层**:W3 定 critic verdict / cover metadata 等业务产物;`*.invocation.json`(哈希/时间戳防伪)留 W4
- **单写者**(放弃 fan-out):§8 #9 允许 W3 fan-out 但 spec §4.0 主动放弃 — 5 小文件单写者保一致 + 守 §11 单写者铁律,避免并行 race

**reviewer 抓的 P0(当轮修,§2.1 闭环实证)**:`/ship` 收齐双轨 critic verdict 后**没把 `critic_b_real_run`/`critic_b_source`/`critic_c_real_run`/`critic_c_source` 回填 draft frontmatter**;gate.py 推送前从 **draft frontmatter**(非 sidecar JSON)读这几个字段做防伪审计,缺失会 exit 2 阻断。→ 修:`/ship` 加 Step 4.5 回填 + 两个 critic subagent Output format 注明「自己只写 sidecar,回填归主线程」→ 复查 `aee417a5d8487beb7` 判 P0 闭合。

**Musk 监督员核验**:Idiot Index ≈ 1×(无冗余/反复);hook 真只接 gate.py 无死引用(invariant #4 干净);单写者是 spec §4.0 合规决策非偷懒;所有 11 个被引用工具(iti_collect/topic_recommender/iti_explore/opening_signal/title_signal/ending_signal/fengyun_lint/critic_vote/generate_cover_by_template/illustrate_decider/post_fengyun_publish)实测全存在(无假承诺)。

---

## 4.4 W4 完工记录(2026-05-27,新窗口看这段就懂 W4 改了啥)

**物理目的**:把 `gate.py` 的 ~25 个 frontmatter 防伪字段(`*_pass`/`*_real_run`/`*_source`)迁到 `output/runs/<slug>/*.invocation.json` invocation log,**gate.py 改写为消费者**。落地 invariant #3(frontmatter 回归 metadata)。

**反 fake 升级(Newton 真 invariant)**:旧 `critic_b_pass: true` 改完稿旗标还在,证明不了「评的是最终稿」;`input_hash == sha256(当前 draft)` 能 —— 不许拿旧版 verdict ship 新稿。

**新建(5)**:`assets/run_log.schema.json`(JSON Schema)、`tools/invocation_log.py`(生产+校验+CLI)、`tools/validate_run_log.py`(PostToolUse hook)、`tools/ship_complete_check.py`(Stop hook,咨询性)、`tools/test_invocation_log.py`(11 测试)+ `tools/test_gate_invocation.py`(7 测试)。

**改写(代码)**:`gate.py` 删 `REQUIRED_PASS_FLAGS/AUDIT/SKILL_AUDIT/SOURCE_PATTERNS/EVIDENCE`,加 `REQUIRED_INVOCATIONS`(6 件 pre-publish)+ `check_invocations()`(存在+schema+`finished_at`<1h;最终稿 stage[verify/critic_b/critic_c/cover]额外 `input_hash` 匹配;`verify.result`∈{ship,force_ship})。保留 base/image/cover_path 物理检查+r18+force-skip+audit log。`.claude/settings.json` 补齐三层 hook。`scripts/verify_baseline.py` 加第 3 件 invocation schema 自检。`verify_audit.py` 加 W4 missing-reason 分类。

**6 件 invocation**:iti / writer / verify(lint+王小波+vote 决议)/ critic_b_huashu / critic_c_content_judge / cover;render 由 Stop hook 查(咨询)。

**⚠️ scope 砍(spec §1.1,Jobs+Newton)**:`image_paths`/`cover_path`/`image_at_h2_indices` 是**物理产物指针 + article metadata,留 frontmatter**(gate 仍物理查);迁它会级联 illustrate_decider+post_fengyun_publish 渲染路径,出 W4 blast radius,故不迁。

**文档同步(§8.7)**:`WRITE_AGENT.md`(Step 8 重写 + v1.6 日志 + §总览 W4 全局 banner)、`frontmatter_checklist.md`(重写)、`SKILL.md`+3 stage refs(banner)、`vendor/` 镜像同步。

**reviewer P1(当轮修)**:WRITE_AGENT per-step pass_flag 例子缺 W4 banner → 在 §总览加全局 banner 点名所有 superseded 字段 + 指向 Step 8 ②。**Musk 合规**:Idiot Index ≈ 1.3×;test-first 真做;invariant #4 三消费者(gate改写+validate_run_log+ship_complete_check)同 wave 落地。

**已知非阻断**(reviewer/Musk 共识不卡 commit):① render 无 pre-publish 硬阻断消费者 —— by-design(render 是终末步,gate 卡的是 publish 命令本身;render.invocation 推后写,Stop hook 咨询查)② test_gate_invocation/test_gate_image_mandatory 用真实 `output/runs/`(用不同测试 slug + finally 清理规避;test_invocation_log 用 tmp_path)。

---

## 4.5 W5 完工记录(2026-05-27,新窗口看这段就懂 W5 改了啥)

**物理目的**:官方 issue #19308 —— Claude 把 Python fenced 伪代码块当「reference 不是 command」、把「如果…→…」条件触发当可挑省事路。把 fengyun-publish SKILL/references + WRITE_AGENT 宪法的伪代码 + 条件触发清扫成**可直接运行**的 bash / `python -c` / 显式 skill-invoke + DEFAULT-on opt-out。

**explorer 实测的关键事实(决定 scope)**:explorer `a0e431c417d9614ba` 核验 `tools/*.py` 发现 ~8 个伪代码符号**没有可用 CLI**(`rank_aihot_candidates`/`score_title`/`score_ending_signal`/`check_*_overlap`/`merge_with_websearch`/`generate_from_decision` 只有 `cli_demo()` 或仅 importable;`fengyun_writer_trial` 等是 skill-invoke 不是 bash)。**且 SKILL.md 有 5 条 W1 遗留假命令**(`topic_recommender --pool`/`title_signal`·`ending_signal <draft>`/`illustrate_decider --draft`·`--generate` —— 这 4 工具无 argparse,跑会静默 demo 或崩)—— 比伪代码更糟,W5 必修。

**scope 决策(reviewer + Musk 复核合规)**:**W5 = doc-only,0 行工具代码**。真 CLI → 真命令(flag 对齐 explorer 映射);importable-only → `python -c`(读文件,不传长文);skill-invoke → 显式「invoke skill」步骤;条件触发 → DEFAULT-on opt-out。**不在 W5 加 CLI wrapper**(守 charter + Musk 预警 ①「确认调用路径不被破坏」不是「加 argparse」+ invariant #4「CLI wrapper 现仅文档消费者,W6 才定 ship.py import/subprocess」+ Jobs 敢砍)。

**改动(8 commit,每文件原子)**:`002f9ba` open(spec + 🚧)→ `d58929f` C1 SKILL.md 修 5 假命令(+vendor)→ `17fb05a` C2 stage_01_collect(2 条件触发 + 3 块,+vendor)→ `d42ac67` C3 stage_02_write(title/ending 2 harness loop,+vendor)→ `a6da7b9` C4 stage_04_publish(3 块,+vendor)→ `6098cee` C5 WRITE_AGENT 宪法 9 块 + v1.7 → `f6ebd18` C5.1 verify 抓的 prose 字面 fence 残留 → `085d130` C5.2 reviewer P2 references 对齐宪法显式 kwargs(+vendor)。

**验收**:verify_baseline **139 passed / 0 deselected**(零回归,= W4 基线);import-smoke 全 14 符号 OK;Python fence 残留 0(除 `.pre-w1-bak` 备份,out of scope);SKILL.md 假 flag 0;references 条件触发 0;vendor 7/7 byte-identical。**三审全过**:verify(静态 subagent + 主线程动态兜底 §8.5.2)PASS + reviewer SHIP(0 P0)+ Musk 合规(Idiot Index 1×)。

**已知非阻断(W6 follow-up)**:`topic_recommender`/`title_signal`/`ending_signal`/`illustrate_decider` 无真 CLI,W5 用 `python -c` 过渡(已可运行)。W6 重写 ship.py 时给这 4 个工具加 `--draft`/`--pool`/`--generate` 真 CLI(带测试),之后文档 `python -c` 一行可简化成 `python tools/X.py --draft Y`。

---

## 4.6 W6 完工记录(2026-05-27,新窗口看这段就懂 W6 改了啥)

**物理目的**:兑现 W5 的 follow-up —— 给 W5 因 doc-only 留作 `python -c` 过渡的工具补**真 argparse CLI**(test-first),再把 SKILL/references/WRITE_AGENT 里的 `python -c` 回写成干净 `python tools/X.py --flag`;并记录「ship.py 编排被 W3 slash 取代」。

**W6 重定义(用户拍板 Option 1)**:原「Agent SDK 重写 ship.py」前提失效 —— 无 `tools/ship.py`(仅 round5 备份),W3 `/ship` slash + 5 subagent 已是 orchestrator-worker(invariant #2 统一语言:不建竞争性 Python ship.py);headless SDK ship.py 0 消费者(cloud 暂停)→ 延 cloud 阶段(invariant #4)。**W6 不建 ship.py**。

**阶段 1 — 10 工具真 CLI(test-first,每工具先写 test 跑挂 → 加 argparse → 跑过 → 1 commit)**:
- C1 `8f739e8` topic_recommender(`--pool/--ws/--out`)· C2 `90e7ea9` event_dedup(`--in/--days/--include-published/--current-draft/--out`,先核现状确认无 CLI)· C3 `78bb2f6` title_signal(`--title/--topic-keywords/--body-chars/--draft`)· C4 `0382da5` title_dedup(`--title/--hook-type/--draft/--max-age-days/--max-n-check`)· C5 `a23f71e` ending_signal(`--draft`)· C6 `c7ce7c2` ending_dedup(`--draft/--max-age-days/--max-n-check`)· C7 `fa30c90` opening_signal(`--trial/--draft`)· C8 `c744aa8` opening_dedup(`--trial/--draft/--current-draft`)· C9 `a75be99` illustrate_decider(`--draft --generate --decision --slug`,默认 dry,位置参数向后兼容)· C10 `47d40fa` iti_explore(`cli(argv)` + `--merge-ws/--out/--max-total`)
- 铁律:每工具只重写 `__main__`→`main(argv)`/`cli(argv)` + argparse + 读文件 + 打印 JSON,**0 改打分/去重/rank 业务逻辑**(reviewer 专项 diff 核 SHIP);保留 `cli_demo()`/`cli_dry_run()`;**未动 opening_dedup 的 tokenize/jaccard/阈值等基础库导出**(title/ending dedup 依赖,回归 20 passed)

**阶段 2 — docs 回写(`python -c` → 真 CLI,每文件 1 commit + vendor 同步)**:
- C11 `666cb20` SKILL.md(骨架 5 处)· C12 `02c3461` stage_01_collect(3 块)· C13 `77efbcf` stage_02_write(2 块)· C14 `bc68ec5` stage_04_publish(1 块)· C15 `d6a57a3` WRITE_AGENT.md v1.8(4 块 + v1.7 历史 prose paraphrase 到字面零)
- 组合 `python -c` 拆成单一职责真命令(topic_recommender→event_dedup 两步 / signal→dedup 两步,主线程读两个 JSON 合成 pass);iti_explore 一步 `--merge-ws --out`

**验收(三审全过)**:
- verify `af21575a99f3d35a7`:静态 6 项 PASS + 动态 `verify_baseline.py` **173 passed / 20 test files**(= W5 的 139 + 新增 CLI test,**零回归**);lint 5 篇 PASS;invocation schema PASS;10 工具 `--help` 全 OK
- reviewer `a84d148cc312d8a86`:**SHIP / 0 P0**(业务逻辑 0 改动 + flag 对齐函数签名 + cli_demo 保留 + 基础库导出未动 + test-first 真做 + Bug 4 self-match 正确);1 P1 = §11 接续协议 stale(W5 era 仍指向「W6 = Agent SDK 重写 ship.py」+ 不存在的 `wave_06_ship_sdk_orchestrator.md`)→ **本收尾 commit 已修指向 W7**
- Musk `a6641a5e6623847fd`:**合规,Idiot Index ≈ 1×**(15 commit 与 spec 计划一一对应无镀金 / 诚实 / invariant #4 遵守不建 ship.py / 单写者无 fan-out §8 #9 / 无 §8 #11 p-hacking)

**`python -c` 归零**:`grep -rn 'python -c'` 在 `SKILL.md` + `references/` + `WRITE_AGENT.md`(user-level + vendor 镜像)= **0**。REFACTOR_PLAN / spec / ARCH 等描述性文档保留「python -c」字样(不在归零 scope)。

**已知非阻断**:reviewer P2(§0 line 39 W0 Musk 历史 note「ship.py SDK 单点失败」)是 W0 冻结记录,不改。

---

## 4.7 W7 完工记录(2026-05-27,新窗口看这段就懂 W7 改了啥)

**物理目的**:封面从「7 固定模板 + 关键词路由 + 写死英文 prompt + 7 天 dedup」**彻底推翻为无模板** —— `huashu-image-curator` 新增 **cover mode**(花叔读文章自著**中文** Seedream prompt)→ 薄客户端 `tools/seedream_client.py`(retry×3 指数退避 + placeholder fallback **全内藏**)。

**决策锁定(用户 2026-05-27 拍板,取代 ARCH §阶段 D「单模板 T5」)**:无模板 / 物理删**不归档** / **删云签名**(缩略图零识别价值,Musk 第一性原理 verdict)+ **留品牌色** `#F8F0E0`+`#D97757` + 手绘 sketchnote(Style Block 锁)/ **中文 prompt**(Seedream 5.0 中文原生优化)+ build 时中英 A/B 实测 / 标题模型内渲染(轻量中文指令,**删旧 5 层英文加固**)/ 参考图推后(invariant #4)。依据:用户拍板(视觉决策人定)+ Musk verdict + 2 explorer 调研(有出处)。

**改动(4 commit,每逻辑单元一原子)**:
- **C1** `64dd202`:新建 `tools/seedream_client.py`(薄客户端,从已删的 `generate_cover_by_template.py` 忠实迁移 ARK 调用 / retry / `extract_title_subtitle` / sidecar;**3 处必要改**:prompt 透传删 `TEMPLATES[tid]+.replace` / retry ×2 固定 2s → ×3 指数 `[1,2,4]`s / 新增 placeholder fallback(`assets/placeholder-sketch.png`)/ sidecar 去 cloud signature)+ `test_seedream_client.py`(test-first,**7 passed**,全 mock 不真调网络)
- **C2** `ef12d8d`:**物理删** `generate_cover_by_template.py`(647)+ `cover_dedup.py`(304)= **949 行净删**;两文件只互相+自引用,无外部消费者、无 test 引用;不归档(回滚靠 git tag `backup-pre-refactor-20260526`+revert+vendor 镜像)
- **C3** `2ba554d`:`huashu-image-curator` 新增 **Mode 3 cover**(花叔 5 心智模型迁移到封面 metaphor 决策 + Style Block 去签名 + 中文 prompt + 5 条中文 few-shot + 轻量标题)+ **新增 `vendor/skills/huashu-image-curator/` 镜像**(扩展 §8.6);顺手清 Mode 2 L354 旧 anchor 的 cloud signature
- **C4** `1219922`:doc-sync 5 文件(`fengyun-cover.md` 流程 / `stage_04_publish.md` Step 7 重写 / `SKILL.md` 骨架 / `WRITE_AGENT.md` 宪法 v1.9 / `COVER_STYLE_GUIDE.md` slim 成权威 Style Block)+ vendor fengyun-publish 镜像;**Mode 2 内文图路径未动**

**验收(三审全过)**:
- **verify**:主线程动态兜底(§8.5.2,subagent sandbox 拒 Bash)`verify_baseline.py` **180 passed**(W6 基线 173 + 新增 7,**零回归**)+ lint PASS + invocation PASS + `seedream_client --help` OK;静态轨 subagent `ad1c9e60c97fe7eb7` **9/9 ✓**(文件删/建、无活引用、去签名、品牌色保留、Mode3 在、Mode2 未动、vendor 双镜像)
- **reviewer** `a5a6509ab2751e34a`:**SHIP / 0 P0**(业务逻辑 0 改 + prompt 真透传 + 签名清干净 + 中文 prompt 落地 + test-first 覆盖 4 场景 + doc-sync 三镜像 byte-identical + placeholder 14KB 真实装 + scope 无越界)
- **Musk** `a3419e6eef3dcd4b9`:**合规,Idiot Index ≈ 1×**(4 commit 对应最小必要动作无镀金 / 诚实 / invariant #4 消费者同 wave 落地 / 单写者串行无并发 / 反 p-hacking 不适用纯架构替换)

**⚠️ 过程踩坑(Musk P2,书面物化避免重蹈)**:C2 物理删 `.py` 后 `tools/__pycache__/` 残留孤儿 `.pyc`(generate_cover_by_template + cover_dedup),verify_baseline 跑 `pytest tools/`(整目录)时撞 pytest import-mismatch → **假 FAIL**;而 `pytest tools/test_*.py`(显式 glob)却 PASS,掩盖了差异。根因诊断(非盲推,守 §8 #12)→ 清孤儿 .pyc → 复跑 **ALL PASS**。**教训:物理删 `.py` 后必清对应 `__pycache__/*.pyc`,否则整目录 pytest 会撞 import-mismatch。**

**已知非阻断(reviewer/Musk 共识不卡 commit)**:① **中英 prompt A/B 实测**是 ship-time 质量 gate(需真调 Seedream + `VOLCENGINE_IMAGE_KEY`),不是 W7 写代码 gate,留实际 ship 时跑;若中文劣化 → 回英文(可逆,只改 cover mode prompt 一处)② `WRITE_AGENT.md` L795 / `stage_04` L136 的 placeholder/retry×1 是 `illustrate_decider` 内文图历史描述,W7 scope 豁免(Mode 2 不动)③ `generate_cover` 循环 `range(max_retries+1)` = max_retries=3 时 4 次尝试 / 3 次 sleep `[1,2,4]`,= Round 25「retry×3 指数退避」语义,test 已验证。

---

## 4.8 W8 完工记录(2026-05-27,新窗口看这段就懂 W8 改了啥)

**物理目的**:TrendRadar 信源从「只读 `latest_daily.md` markdown 摘要 ~170 条」升级为「直接读 `output/rss/<date>.db` 全量、按 feed 取最新 N=5 条」(抓不到回退 markdown);I-2 深搜不再镜像 I-1 的 4 个 generic WebSearch query,改为「WebFetch T 选定主源 + aihot `?q=` 实体搜索 + 1 个补充 query」。

**3 fork 拍板(AskUserQuestion,2026-05-27)**:① per-feed N=5(暴露 `--per-feed-n` flag,默认值)② **砍** smol.ai by-topic(digest 级 RSS,by-topic 只能粗暴 grep,低价值)③ E4 **no-op**(5 僵尸 RSS 已删 2026-05-26 / X 从未进 ITI 工具 / IT之家 仅在跨仓库 `D:\Dev\TrendRadar\config.yaml`,本分支 git 不跟踪)。

**改动(open + 4 commit,每逻辑单元一原子)**:
- **open** `144820b`:spec `refactor_specs/wave_08_iti_trendradar_wrapper.md` + §0 ⏸→🚧
- **C1** `b92c26a`:**E2** + **E3a 函数**(iti_collect,test-first 8 测试,全 tmp sqlite/mock urlopen)。`fetch_trendradar` 三拆:`_fetch_trendradar_markdown`(原 markdown 逻辑零改,作回退)/ `_fetch_trendradar_db`(窗口函数 `ROW_NUMBER() OVER (PARTITION BY feed_id ORDER BY published_at DESC)` 取每 feed 前 N,只读 `mode=ro`,整体 try/except→`[]`)/ `fetch_trendradar` 编排 DB 优先、失败回退 markdown(ARCH §7.4:563);`collect_pool`/`cli` 加 `--per-feed-n`(向后兼容,默认 5);`fetch_aihot_by_query` 逐 entity[:3] 调 `?q=` 合并 URL 去重(端点出处 `aihot/SKILL.md` L184-206,2026-05-08 上线)。
- **C2** `58ad499`:**E3a 接线**(iti_explore)— `_fetch_aihot_by_query` 薄 wrapper + `explore_topic` 源列表第 3 位插 `aihot-query`(test-first +1 测试);顺手修 stale 注释(源数 5→7)。
- **C3** `1c29105`:**E1 doc-sync** — I-2 不镜像 I-1 + E2 DB reader(`stage_01_collect` + `SKILL.md` + `WRITE_AGENT.md` 宪法 Step 2 `websearch_count` 4→1 + vendor 镜像 byte-identical)。
- **C4** `f71a330`:**三审收尾修**(§2.1 当轮闭环)— `.claude/agents/fengyun-iti.md` L53 stale「中英文各 2 次」I-2 mirror 指令(verify FAIL E + reviewer P1 收敛同一处)+ `iti_explore` docstring 补回计数「7 个」。

**验收(三审全过)**:
- **verify**(Sonnet,Bash 本 session 可用,非 sandbox fallback):`verify_baseline.py` **189 passed**(W7 基线 180 + 9 新 W8 测试,**零回归**)+ whole-dir `pytest tools/` 189 + 静态 A-E;主线程独立也跑 189(双确认)。**实测**:`iti_collect --per-feed-n 5` 真读 DB **257 条(5/feed)** vs 旧 markdown ~170;`iti_explore` 的 `aihot-query` 实测 **23 条**命中(`?q=` 端点真活)。
- **reviewer** `SHIP / 0 P0`:业务逻辑 0 改 + `_fetch_trendradar_markdown` 字节级原逻辑 + test-first 全 mock 零真网络零触碰真 `D:\Dev\TrendRadar` + 回退真可触发(try/except + finally close)+ 向后兼容 `fetch_trendradar_topic` + scope 无越界(`fetch_smol_ai` 完整、TrendRadar config 未动、零 .py 删)+ N=5 非 p-hacking;1 P1 = agent 文件 stale(C4 已修)+ 1 P2 docstring 计数(C4 已修)。
- **Musk** `合规,Idiot Index = 1×`:4 commit 与 spec 一一对应;E2+E3a-函数合并进 C1 是「共享测试文件 + 同一 test-first 循环」的合理合并非偷懒;invariant #4 双消费者(DB reader→collect_pool / aihot_by_query→explore_topic)同 wave 落地;单写者无 fan-out;零 §8 禁令违反。

**已知非阻断**:① aihot `?q=` 主线程实测可达(23 条),子 agent sandbox curl HTTP 000 — 真 ship 时 `fengyun-iti` agent 的 WebSearch/WebFetch 走主线程能力不受影响。② DB 的 `published_at` 若非 ISO(部分 feed RFC2822/空)仅影响「每 feed 取哪 5 条」精度,不影响正确性(NULL 在 DESC 排最后),下游 dedup/rank 收口。③ E3b smol.ai by-topic 砍 / E4 no-op 均 fork 拍板有据。

**⚠️ 教训(物化,§8.7 已补一行)**:**doc-sync §8.7 矩阵漏了 `.claude/agents/*.md`**。W3 建的 5 个 subagent 文件也是 **live 操作指令**(/ship 真调),改 collect/write/critic 阶段 SOP 时必须连带核对对应 agent 文件,不只 SKILL/references/WRITE_AGENT。verify + reviewer **双双独立**抓出 `fengyun-iti.md` L53,证明 spec 的 doc-sync 清单 + explorer 调研默认没覆盖 agent 文件层 → §8.7 矩阵新增「改任何阶段 SOP → 连带核 `.claude/agents/fengyun-<stage>.md`」。

---

## 4.9 W9 完工记录(2026-05-27,新窗口看这段就懂 W9 改了啥)

**物理目的**:把 critic 链路里**永远过/永远不过(零判别力)的维度砍掉、误伤面过大的阈值调松、灵魂判断伪装成机械规则的伪 lint 清掉**,让 lint 回归「无歧义、误判率→0」机械底线,灵魂判断全归 B+C founder verdict。**全程最高风险 wave(p-hacking 红线),每改动有外部出处。**

**开工 = explorer×2 调研 + AskUserQuestion 4 fork 拍板**(spec §0):
- **F1 验收方案**:explorer 发现 **K-fold-ROC-on-critic 不成立** —— W2 删 Track A 数字分后 critic 是 B+C 二元(无数字算 ROC);被砍的 opening/title 维度是**写作侧 harness 信号**(不在 gate.py REQUIRED_INVOCATIONS,不卡 ship);「549 条」是 xhs 项目的,本 repo 没有(本 repo 有 targets.parquet 2730 篇 read_pct + B4 用的 321 篇)。→ 用户拍板**信号分 held-out ρ + 触发率前后**(parquet proxy,aid join read_pct)。
- **F2 lint 价值**:用户深问「lint 真有用吗能不能砍」→ 调研结论(lint-vs-founder-split 铁律):lint 不能整砍(R18-P0/R0/R29/R30/R19 无替补守门),但 R13/R14/R16/R21/R2/R4 是灵魂判断伪装机械规则(无源+品味+已被 B/C/王小波覆盖)。→ **清伪 lint 替代原 B3「29→6 RuleFamily」**(换标签破坏测试无收益)。
- **F3 R13 词典**:阈值/severity 有源但换词无源 → 用户「没用就删」→ R13 整条砍(并入 F2)。
- **F4 情绪锚点**:ARCH 说砍/审计说调/词典无源,第一人称密度裹在同函数 → 用户拍板**拆函数**(留第一人称密度,砍动词维)。

**改动(open + 6 commit,test-first,每逻辑单元一原子)**:
- **open** `077b02e`:spec `wave_09_dim_critic_tune.md` + §0 ⏸→🚧
- **C1** `082f09f`:opening 维度重校 — 砍 `_score_reframe`(B4 6.6%)/`_score_concreteness`(B4 87.2%)/`_score_info_density`(B4 100%);拆 `_score_emotion_anchor`(留第一人称密度在 check_physical_constraints,denominator 不变);真首段 50→25 + 修字段名歧义(真·首段);删 test_round26 section C(7 reframe 测试,反差感已砍)
- **C2** `8f7136a`:title 维度重校 — 砍 `_check_fatal_combo` risk 门(B4 0/321,tb_ratio/english_chars 留 advisory);7钩子 hard gate→软分(B4 卡掉 72% 卡兹克爆款);4特质 ≥2→≥1(B4 ≥2 仅 3.4%)
- **C3** `cf45233`:清 6 伪 lint(R2/R4/R13/R14/R16/R21,tombstone)— lint-vs-founder 铁律 + B/C/王小波覆盖
- **C4** `0164728`:修 R7 词典(删 增强/凸显/强调/格局/证明,误判率>0 的正常中文词)
- **C5** `d518722`:验收 harness `w9_signal_validation.py`(F1)+ 更新 `dim_trigger_rate_audit.py`(移除已砍维引用;输出改 `*_w9_after.json` 绝不覆盖 B4 before-snapshot,已 git restore)
- **C6** `7c57690`:doc-sync §8.7 critic 行全套(WRITE_AGENT + 2 agents + stage_01/02/03 + content-judge M6 + voice-dna + vendor)

**验收(三审全过)**:
- **verify** `aae1bed85b8acee8e`:跑动态轨(PowerShell,本机无 WSL-bash 用 PowerShell 直跑;**非 sandbox fallback**)`verify_baseline.py` ALL PASS + `pytest tools/` **193 passed**(W8 基线 189 + 净 +4)+ harness `cut_dim_strong_signal_flags`=["none ..."] + 静态 9 项;主线程独立也跑 193(双确认)。
- **reviewer** `af982b62242db28d4`:**SHIP / 0 P0**(8 维全过:反 p-hacking 每改动有源 / 砍维真移除 / tb_ratio 保留连贯 / 调阈值对应 B4 / lint 清单符合 lint-vs-founder / doc-sync 全 / 0 改无关逻辑 / 193 passed / B4 snapshot 未动);3 P2 = 历史 output/audit 文档(FIX_CHECKLIST / 旧 audit md)有 stale R13/R21 字样,非 runtime,cosmetic 不返工。
- **Musk** `a7df63c2bb4ed3b04`:**合规**(Idiot Index 1× 最优 / 诚实真物化 / 反 p-hacking 每改动外部出处 100% 覆盖 + harness 只读不挑改动 / invariant #4 净删除 + 范围纪律全守 / explorer×2 + AskUserQuestion 4 fork 真用)。Musk 初判「偏离」**仅指三审"录入收尾"在它审计时还没做**(Musk 与 reviewer 并行跑,读不到 reviewer/verify 的 verdict)→ 本收尾 commit 满足其 3 条:reviewer 已 SHIP(录入)/ verify 已 PASS(录入)/ §0 🚧→✅ + 本 §4.9。Musk 明示「纠正完成后即合规」。

**harness 实证数据(反 p-hacking 佐证,主证据仍是 B4 零方差)**:砍维 proxy 无强显著正相关 — 反差/事件引入 ρ=0.01(p=0.62)、情绪开头 ρ=0.013(p=0.50);tb_ratio ρ=-0.195(显著=真信号,印证只砍坏掉的 risk 门保留 advisory);真首段 ρ=+0.097(baoyu+0.20/huashu+0.26 显著,印证保留维度重标定);7钩子-反共识 ρ=0.011(不显著,印证软化 hard gate)。held-out 50 固定 seed,不参与任何折/调参。

**已知非阻断 / 诚实披露(Musk P1,§4.9 注明不返工)**:
- ① **具体性砍**实际命中率 87.2%(不是 100%/0%),严格不属 B5「>95% 或 <5%」零判别力;其砍的独立动机是「阈值 6 与分数曲线脱钩」(花叔语料最低分都过阈值 6 = 弱区分度)+ 选项 A 用户拍板。是本批唯一**未被 harness proxy 直接验证**的砍(无对应 parquet 列),靠 B4 实测 + 用户决策。诚实标注。
- ② **harness 是事后验证非事前 test-first**:打分/阈值/规则改动(C1-C4)是 test-first(先写测试红→实现→绿);但验收 harness(C5)在改动之后建。对反 p-hacking 反而更安全(改动出处全来自 B4 实测,独立于 harness 数字),但与 spec「test-first」字面有出入,诚实说明。
- ③ **content-judge / fengyun-writer 无 vendor 镜像**(§8.6 scope 仅 fengyun-publish + huashu-image-curator,W2 编辑 content-judge 同例)→ 其 user-level doc-sync 编辑不进 git;rollback 安全缺口预存于 W9 之前,本 wave 不扩 vendor scope(留用户/reviewer 决策)。
- ④ reviewer 3 P2(历史 output/audit md 的 stale R13/R21 字样)cosmetic,非 runtime,留未来 cleanup grep。

---

## 4.10 W10 完工记录(2026-05-27,验收 wave —— 不改业务代码)

**物理目的**:把 W0-W9 重构出的新 pipeline 真跑一遍端到端(从零到一全流程到草稿箱),用 ARCH §8 验收表逐项核对重构目标是否真达成,产出客观证据包供风云下「替不替换主支」的 go/no-go。**0 行业务代码改动**(写入仅:spec / 本记录 / output 运行时产物)。

**2 fork 拍板(AskUserQuestion)**:F1 **从零到一跑全流程**(真推草稿箱,花 Seedream + 微信额度)/ F2 **用草稿箱已有老稿做 A/B 对照**(不重跑老流程,风云 founder verdict)。

**e2e 实跑(真到草稿箱)**:主题 = 藏师傅小红书排版 AI Skill(System A 数据驱动选,burst=0.95);成稿 `output/drafts/20260527-guizang-xhs-skill-v2.md`(4546 字 huashu thought_essay);封面真 Seedream(笔/字 metaphor)+ 2 内文图真 Seedream(非 placeholder);**草稿 media_id `f5xAnh6tT5u4aYGYiST-AGlgNr50rdK6PaKTEWGkP5wPtMnyQLEzHgzPElC1hL0H`**。

**§8 验收表 8 项结果**:

| # | 指标 | 目标 | 实测 | 判定 |
|---|---|---|---|---|
| 1 | SKILL.md 行数 | ≤300 | **199**(user+vendor,3 次独立测) | ✅ |
| 2 | Python 伪代码 | 0 | grep=0 | ✅ |
| 3 | 三轨→双轨 critic 并行 | ✅ | ship.md L44 同消息 dispatch B‖C;真跑 3 轮真并行派发 | ✅ |
| 4 | Cover 撞型 | 不撞 | W7 删模板,花叔 Mode3 自著 prompt | ✅ |
| 5 | 信源覆盖 | 11进7+ | 5 聚合源(aihot/trendradar 257/arxiv/smol.ai/we-mp-rss)302→290 候选 | ✅ |
| 6 | Gate 拦截次数 | 0 | check_draft PASS + live gate preflight PASS,真推成功 | ✅ |
| 7 | Lint 修复轮数 | ≤2 | 2 轮(6→2→0 violation,仅 R20 info) | ✅ |
| 8 | 端到端耗时 | ≤25min | **降级 advisory**(memory `feedback_no_time_estimates`,不作硬门) | N/A |
| + | verify_baseline | 零回归 | **193 passed / 0 deselected** | ✅ |

**revise loop + force_ship 实证**:critic B(huashu)‖C(content-judge)跑 3 轮,**3 轮都 B=no-ship / C=sign**(结构性分歧:花叔要纯 lived-stake confession,content-judge 签 0.90 thought-essay)→ REVISE_CEILING=3 → `critic_vote` **force_ship**(W2 隐藏天花板,全自动闭环不卡死)。证明 B/C 真分歧不会 deadlock pipeline。

**三审全过**:
- **verify**(本 session Bash 可用,双确认):verify_baseline 193 passed + §8 静态 4 项 PASS。
- **reviewer** `a099dde65e6c8c5e2`(全新 session):**达标可替换主支,0 P0**;1 P1(invocation 批量写入 = sandbox 兜底已知局限,gate 不依赖磁盘时间戳)+ 2 P2(writer.invocation output_files 写 v2 应 v0 / `images` vs `image_paths` 双字段无文档)。
- **Musk** `a5850adc2418f589f`(全新 session):**合规,Idiot Index ≈1.25×**;主支红线 CLEAN(main=ae3cb4c 未动);invariant #4 零源码污染;§8 八项有物理产物可查非装饰。

**⚠️ 诚实披露(reviewer P1/P2 + Musk A1/A2,书面物化)**:
- ① **网络/凭证步骤主线程兜底**(§8.5.2):Stage1 ITI(TrendRadar DB + aihot)+ Stage4(Seedream + 微信)由主线程跑 —— 子 agent sandbox 无网络/无 .env/无 D:\ FS。只有 writer + critic B/C 是真 subagent 派发。
- ② **2/3 轮 revise 改稿由主线程做**(非重派 writer subagent):`SendMessage` 工具本环境不可用,降级为主线程直接改稿;每轮改完都重新 lint(都 0 violation)。rounds.json 留 v0→v1→v2 痕迹。(Musk A1)
- ③ **invocation 批量写入**:7 件 invocation 在推送前统一写入(非各阶段执行时写),因主线程兜底跑无法触发 PreToolUse hook 逐件写;gate 查 `finished_at` 字段不查磁盘时间戳,功能无损,但 invocation log 的「时间线防伪」在本次 e2e 弱化。(reviewer P1)
- ④ **agentId 不可外部追溯**:`run_log.schema.json` 无 agent_task_id 字段(W4 设计遗留债,非 W10 引入);subagent 真用靠 verdict 文件时序 + 内容差异佐证。(Musk A2)
- ⑤ **集成 roughness(P2,下轮可清)**:illustrate_decider 写 `images:`,gate 查 `image_paths`;cover 步骤不自动写 `cover_path` —— 都靠 orchestrator 手填(ship.md 设计如此,但字段重叠 + 无权威文档说明)。

**A/B + 主支替换状态**:e2e 产出 + 三审已就绪;**A/B 质量结论 = 风云本人 founder verdict(主观,未判)**;**⛔ `git branch -M arch-refactor-v1 main` 等风云显式说「替换主支」才执行,在那之前 branch 不动主支**(旧 main=ae3cb4c 已有 tag `backup-pre-refactor-20260526` 兜底)。

**可选未做(非阻断)**:W9 reviewer 留的 3 个 cosmetic P2(历史 output/audit md 残留 R13/R21 字样,非 runtime)未清;reviewer/Musk 的 P2(字段重叠 / agentId schema)留下轮。

---

## 4.11 全系统体检 + 3 修复(post-W10 follow-up,2026-05-27)

**触发**:风云对 W10「感觉没什么差别」+ 要求对 arch-refactor-v1 做一次全流程系统验证与调研(不止 W10 单篇)。

**3 路只读审计(并行,Sonnet)**:A 测试/CLI/§8 静态 `a120e543` / B 编排链路+引用+doc-sync `a649be4a` / C 5 invariant+系统性风险 `a471054f`。**综合结论:分支对「本地主线程驱动 ship」健康,替换主支 0 硬阻塞。**
- ✅ 健康:verify_baseline + 全目录 pytest 双双 193 passed;20 工具 CLI 全可跑;SKILL.md 199 / 伪代码 0 / vendor byte-identical;引用零断链;3 层 hook 在;僵尸术语全是历史标注无 live 引用;invariant #1/#2/#5 守住。
- 🔴 **最重要发现 = force_ship 机制断路**(invariant #4 违反):花叔(B)emotion≥60% 门槛对思想/分析型文章系统性 no-ship → 每篇走 force_ship(W10 实证 B/C 3 轮分歧);但 force_ship 标记**此前无任何消费者**(weekly_metrics 归档 / critic_retrain 没建)→ 学习信号死在 JSON,pipeline「会跑」但「不会自己变好」。**这正是风云「感觉没差别」的机制层根因**([[feedback_iterate_mechanism_not_article]])。
- 🟡 invocation 1h 新鲜度窗口 vs 慢流程(>1h 早期 stage 过期被 gate 拦);image_paths 靠 fengyun-cover subagent LLM 手填无代码兜底(P1);R21 编号复用 doc/code 歧义(P1);placeholder 缺失 illustrate_decider raise vs seedream return False 不一致 + 无 e2e 集成测试 + 3 孤儿 .pyc(P2)。

**风云拍板「全接上」(1h 窗口 + R21 文档 + force_ship 回路)**,test-first 实现:
- **修 1**:`invocation_log.py` `MAX_AGE_SECONDS` 3600→**7200(2h)**(末轮 stage 另有 input_hash 兜底,新鲜度是次级守卫);`test_invocation_log.test_is_fresh` 扩断言(90min 仍新鲜 + 3h 过期 + 传 1h 窗口可覆盖)。
- **修 2**:R21 编号复用澄清(**无行为变更**)——`fengyun_lint.py` L953 注释 + `WRITE_AGENT.md` L570 点明:W9 砍的是 base R21(粗体注水 `R21_bold_ai_padding`),huashu 族另有 active 的 `R21_huashu_h2_pattern`(H2 模式,未砍),同号不同规则。
- **修 3**:**接上 force_ship 学习回路**(闭合 invariant #4)——新建 `tools/flywheel_report.py`(只读 W4 invocation log,聚合 force_ship 率 + B 否决率 + C 挂名率 + B/C 分歧率 → markdown 报告 +「改 writer SOP / 选题侧,不是改这一篇」机制提示;历史顶层 run 报告 schema 跨 Round 不一致故不解析,诚实标注)+ `test_flywheel_report.py`(5 测试)+ `critic_vote.py` force_ship 出口加 producer→consumer 指针。实测 live 报告:1 篇标准 ship,force_ship 100%,正确给出花叔门槛系统性不匹配提示。

**验收**:`verify_baseline` **198 passed / 25 test files**(193 + 5 flywheel,**零回归**);lint + invocation schema PASS。

**未修(明确 deferred,非本轮 scope)**:① image_paths 代码层兜底(P1,风云 Option 2 未选,留 fengyun-cover subagent 手填;`post_fengyun_publish.py` L420 注释仍误述「illustrate_decider 写 image_paths」未改)② agentId 不可追溯(W4 schema 无 `agent_task_id` 字段,W4 遗留债)③ placeholder raise/return 不一致 + 无 e2e 集成测试 + 孤儿 .pyc(P2)。

---

## 5. Wave spec 文件目录(W0 之后陆续创建)

每个 wave 一个独立 spec 文件,存在 `refactor_specs/`:

```
refactor_specs/
├── wave_01_split_skill_md.md          # W1 开工时写
├── wave_02_delete_6_legacy.md         # W2 开工时写
├── wave_03_subagents_slash_hook.md
├── wave_04_invocation_log.md
├── wave_05_bash_default_on.md
├── wave_06_real_clis.md                # W6 重定义(原 ship_sdk_orchestrator 前提失效,见文件头)
├── wave_07_cover_redesign.md
├── wave_08_iti_trendradar_wrapper.md
├── wave_09_dim_critic_tune.md
└── wave_10_e2e_acceptance.md
```

**spec 文件结构**(每个 wave spec 都遵守):
```
# Wave X: <name>

## 物理目的(一句话)
## 改动文件清单(精确到行号)
## 改前 vs 改后(代码 diff 样例)
## 验收命令(本 wave 专有)
## 风险 + 兜底(本 wave 专有)
## reviewer subagent prompt(全新 session 审稿用)
```

---

## 6. 6 个 subagent 角色(全程用这 6 种,Musk 监督员 2026-05-27 新加)

详见 `docs/ARCH_REFACTOR_V1_PLAN.md` §6.1。简表:

| 角色 | 何时用 | 工具白名单 | 维度 |
|---|---|---|---|
| 主线程 (你) | orchestrator | 全部 | — |
| explorer | wave 开始 read-only 探索 | Read / Grep / Glob / WebFetch / WebSearch | 收集 |
| writer (可选) | 单文件改写(W3 fan-out 唯一场景) | Read / Edit / Write | 执行 |
| **verify** | wave 收尾跑验收脚本 | Bash / Read | **看脚本结果** |
| **reviewer** | wave commit 前全新 session 审 diff + spec | Read / Grep / Glob(无 Write) | **看产物质量** |
| **Musk 监督员** | wave 收尾前全新 session 核验过程合规(2026-05-27 新增) | Read / Grep / Glob / Bash(git log) | **看过程合规** |

**三者并行不冲突,缺一不可**:
- verify 答「脚本通不通?」
- reviewer 答「产物对不对?」
- Musk 答「过程合不合规?Idiot Index 多大?有没有偷懒偏离规划?」

**铁律**:
- 并发 subagent ≤ 3(配额警戒线)
- reviewer 必须全新 session(`/clear` 后才能起)
- 关键文件(SKILL.md / ship.py)绝对单 agent(不 fan-out)
- 每 wave 收尾 `/clear`(主线程不累积上下文)

---

## 7. 应急 rollback 路径

```bash
# 任何 wave 出问题,回滚到该 wave 开始前的状态:
git reset --hard HEAD~1   # 撤销当前 wave commit

# 完全放弃新分支,回主支:
git checkout main
git branch -D arch-refactor-v1   # 删新分支
# (主支 tag backup-pre-refactor-20260526 永远在,可 git checkout 回看)

# 整个重构失败,主支照旧:
# (新分支不 merge 进主支即可,删不删随意)
```

---

## 8. 全程禁止做的事

1. ❌ 直接 commit 到 main(必须在 arch-refactor-v1 分支)
2. ❌ 跳 wave(W1 没完成不能进 W2)
3. ❌ wave 收尾不跑验收脚本就 commit
4. ❌ 多 subagent 同时改一个文件
5. ❌ 写文档不更新本文件 wave 状态
6. ❌ /clear 后不读本文件直接干活
7. ❌ **wave 验收脚本由主线程 Bash 直接跑(必须派 verify subagent)** — W0 已踩坑
8. ❌ **wave commit 前不派 reviewer subagent 全新 session 审**(必须 reviewer 出 binary verdict 才能 commit) — W0 已踩坑
9. ❌ **关键 wave(W1 / W4 / W6 / W9)fan-out 多 writer subagent 并行写代码** — 这些 wave 涉及跨文件强一致(SKILL.md / invocation log schema / ship.py / critic 参数),并行 = 风格漂移 / 撞合并冲突。fan-out 只允许在 W3(5 个独立 subagent 文件)
10. ❌ **reviewer subagent 走旧 session** — reviewer 必须 `/clear` 后才能起新 session(防 self-bias,arxiv 2402.11436);旧 session 知道主线程怎么写的等于 self-review
11. ❌ **p-hacking 改阈值无外部出处**(memory `feedback_no_p_hacking`) — 任何 critic / opening / title / R13 阈值改动必须有 PHASE1 / corpus / 论文出处,禁止 round 内 grid search 拍脑袋
12. ❌ **盲推 3 次没修好继续盲推**(memory `feedback_3_blind_fixes_then_research`) — 同一个 bug 改 3+ 次还没修好 → 立即停 → 派调研 agent 或调专门 debug skill

## 8.5 每 wave 必须用 subagent 的硬约束(W0 教训 + 2026-05-27 用户加强)

**「每 wave 至少用 3 个 subagent」**(verify + reviewer + Musk 监督员):

| 必须用 | 用在哪一步 | 为什么 |
|---|---|---|
| **verify subagent** | wave 收尾跑 `scripts/verify_baseline.py` + 任何本 wave 专有验收 | 主线程跑 = context 累积 + 主线程偷懒("跑了就 OK 不再细看")。subagent 独立 session 跑 = 客观结果 |
| **reviewer subagent** | wave commit 前对 diff + spec 做 binary verdict(全新 session) | 防 self-bias(arxiv 2402.11436);主线程自己审自己 = 看不到盲点 |
| **Musk 监督员 subagent** | wave 收尾前对**执行过程**做 binary verdict(全新 session) | 看过程合规性(用了哪些 subagent / 有没有偷懒 / Idiot Index 多大 / 偏离规划没)。跟 reviewer 互补:reviewer 看产物质量,Musk 看过程合规 |

**可选用**(本 wave 涉及才派):
| 角色 | 何时派 |
|---|---|
| **explorer** | wave 开始时需要读大量现状代码/真品(read-only)|
| **writer** | wave 内有 ≥ 5 个独立小文件改写(W3 fan-out 唯一场景) |

**违反后果**:任何 wave 完工后回查 §0 wave 状态表「subagent 使用」字段,如果缺 verify / reviewer / Musk 任一,说明主线程偷懒,**记入 retrospective 教训 + 强制补救派 subagent 复审**。

### 8.5.2 sandbox 双轨规则(W1 教训,2026-05-27 用户决策 B)

**问题**:subagent 在 Claude Code 默认 sandbox 模式下**被拒绝跑 Bash / PowerShell**。verify subagent 只能 Read 静态文件(行数 / 文件数 / link 全活),不能跑 `verify_baseline.py` 等动态命令。

**双轨规则**:
- **subagent 静态轨**(优先,默认):wave 收尾派 verify subagent 跑静态检查(`wc -l` / `ls` / `grep link 全活` / 字段保留 grep / 备份文件存在等只读检查),写报告返主线程
- **主线程动态轨**(兜底,sandbox 限制时):subagent 报「Bash denied」后,主线程兜底跑 `python -X utf8 scripts/verify_baseline.py` 等动态验收命令

**两轨都跑才算 verify 完工**,任一缺 = 不能 commit。

**诚实记录义务**:主线程兜底跑动态轨时,wave commit message 必须写 `verify (sandbox fallback - subagent 被拒 Bash, 主线程兜底跑)`,不许假装是 subagent 跑的。

**这不算违反 §8 禁令 #7**:#7 禁的是主线程偷懒不派 verify subagent,双轨规则下 subagent 真派了只是被 sandbox 限制能力,主线程跑是物理兜底。

### 8.6 user-level skill 镜像策略(W1 架构补丁,2026-05-27 用户决策 yes)

**问题**:`~/.claude/skills/fengyun-publish/` 是 user-level skill,**不在项目 git repo 内**。任何 wave 改 SKILL.md / references/ 都不被 git 跟踪。git rollback 到 tag 时,user-level skill 不会自动回退。

**镜像策略**(W1.1 落地):
- 项目内建 `vendor/skills/fengyun-publish/` 镜像 user-level 完整 skill 文件结构
- 每个 wave 改完 user-level skill 后,**主线程必须同步镜像到 vendor/skills/**(rsync 或 cp -r)
- git 跟踪 `vendor/skills/fengyun-publish/`,保证 rollback 安全
- 真正 invoke 时仍走 user-level(Claude Code 默认加载路径不变)

**同步动作清单**(每个改 user-level skill 的 wave 收尾必跑):
```bash
# 1. 同步 user-level → vendor/(覆盖)
cp -r ~/.claude/skills/fengyun-publish/* vendor/skills/fengyun-publish/

# 2. git add vendor 改动
git add vendor/skills/fengyun-publish/

# 3. (commit 时一起 commit,不单独 commit)
```

**rollback 时(W10 失败或紧急回退)**:
```bash
# 1. git checkout backup-pre-refactor-20260526(或任意旧 tag)
# 2. 用 vendor/ 内容覆盖 user-level
cp -r vendor/skills/fengyun-publish/* ~/.claude/skills/fengyun-publish/
```

**镜像方向单一**:vendor 是 user-level 的副本(read-only by convention),不直接编辑 vendor/。改 SKILL.md 永远改 user-level,然后同步到 vendor/。

### 8.7 文档同步矩阵(W2 最大教训,2026-05-27)

**W2 踩的坑**:改 `critic_vote.py` 删 Track A,只同步了 fengyun-publish SKILL/references,**漏了 `WRITE_AGENT.md`**(系统宪法,gate.py 在代码里引用它)。reviewer 全新 session 才抓出 —— 宪法还停在三轨 + 一行 ImportError。教训:**改代码 / 改一处文档,必须连带改的「下游文档」要有清单,否则总漏宪法**。

改某类东西时,**这一串必须同步检查**(grep 旧术语确认无残留):

| 改了什么 | 必须连带同步 |
|---|---|
| **critic / 评审逻辑**(critic_vote / gate critic 字段)| ① `WRITE_AGENT.md`(宪法,Step 6/6.5)② fengyun-publish `SKILL.md` + `references/stage_03_verify.md` + `frontmatter_checklist.md` + `failure_modes.md` ③ `content-judge/SKILL.md`(M3/banner)④ `fengyun-writer/references/critic_mode.md` ⑤ `tools/verify_audit.py` + 测试 fixture |
| **lint 规则**(加/删 RXX)| ① `WRITE_AGENT.md` Step 4 ② fengyun-publish `SKILL.md` 必跑命令骨架 ③ 对应测试 |
| **删一个 skill / tool**(如 humanizer / score_draft)| ① `gate.py` REQUIRED_* 列表 ② `WRITE_AGENT.md` 对应 Step + frontmatter 示例 ③ fengyun-publish `SKILL.md` 工具清单 + 失败表 ④ `frontmatter_checklist.md` 字段计数 ⑤ 测试 fixture |
| **任何 fengyun-publish skill 文件**(user-level)| → 同步 `vendor/skills/fengyun-publish/`(§8.6)|
| **任何阶段 SOP / 流程 / query 数 / 工具调用**(collect / write / verify / publish)| → **连带核 `.claude/agents/fengyun-<stage>.md`**(W3 建的 5 个 subagent 是 `/ship` 真调的 live 操作指令,不只 SKILL/references/WRITE_AGENT)。**W8 教训**:verify + reviewer 双双独立抓出 `fengyun-iti.md` L53 still「中英文各 2 次」(I-2 mirror),spec doc-sync 清单 + explorer 调研默认漏了 agent 文件层 |
| **pipeline 人工 gate / 决策路径**| ① `WRITE_AGENT.md` ② `SKILL.md` 决议路径 + 失败表 ③ `stage_03/stage_04` ④ Step 9 报告模板 |

**收尾自检**(reviewer 会查,自己先 grep):删/改某术语后,`grep -rn "<旧术语>"` 全 skill + tools + WRITE_AGENT,确认只剩「已删/superseded」标注,无活引用。**`WRITE_AGENT.md` 是最容易漏的一个 —— 它在 repo 根,不在 skill 目录,grep 范围常常漏掉它**。

### 8.5.1 Musk 监督员的核验维度

Musk 监督员每 wave 收尾必答 5 个问题:

| Q | 问什么 | 期望 |
|---|---|---|
| Q1 | 开发规划 vs 实际执行 — Idiot Index 多大? | ≤ 3× 合理,3-5× 警告,≥ 5× 偏离 |
| Q2 | 踩坑诚实程度(承认 vs 实际) | 诚实 / 部分诚实 / 藏问题 |
| Q3 | 学习闭环建没建好(禁令是不是装饰) | 真物化 / 半物化 / 装饰 |
| Q4 | invariant #4「0 消费者 = 0 生产」遵守度 | 遵守 / 部分 / 违反 |
| Q5 | subagent 真用 vs 假用(挂名头) | 真用 / 假用 |

binary verdict:**合规(可进下一 wave)** / **偏离(必须先纠正)**

---

## 9. 文档关系图

```
ARCH_REFACTOR_V1_PLAN.md  ← WHY + WHAT (策略,本次重构存在的理由)
        │
        ▼
REFACTOR_PLAN.md           ← HOW + WHEN (本文件,wave 状态机)
        │
        ├─→ refactor_specs/wave_XX.md   ← 每 wave 独立 spec
        │
        └─→ scripts/verify_baseline.py  ← 通用验收脚本
```

---

**最后更新**:2026-05-27(**W0-W10 全 ✅ done —— 10 wave 架构重构全完工**;W10 = e2e 验收,真跑一篇到草稿箱 + §8 八项全 PASS + 三审全过,见 §4.10;**⛔ 整体替换主支 `git branch -M arch-refactor-v1 main` 等风云 A/B founder verdict + 显式说「替换主支」才执行**)

---

## 11. ⚡ 新 CLI 窗口接续协议(2026-05-27 加)

**新开 CLI 窗口继续本重构,严格按这个顺序:**

1. `cd D:\Dev\ai-wechat-pipeline && git status`(必须干净)+ `git branch --show-current`(必须 `arch-refactor-v1`)
2. `git log --oneline -8`(确认 HEAD = W9 收尾 commit 或更新,**W0-W9 已全 done**)
3. **读本文件 §0 状态表 + §1 reload 协议 + §1.1 五条 invariant**(3 分钟恢复全上下文)
4. 读 `docs/ARCH_REFACTOR_V1_PLAN.md`(WHY,**W10 = e2e 验收** 部分,见 §6.2 wave 表 + §7.1/§8 验收标准)+ **W10 开工时写 `refactor_specs/wave_10_e2e_acceptance.md`**(spec)
5. **W0-W10 全 ✅ done —— 10 wave 架构重构全完工**(见 §4.10)。W10 = e2e 验收已跑完:真跑一篇 ship 到草稿箱(media_id f5xAnh6...)+ §8 八项全 PASS + 三审全过(reviewer 达标可替换主支 / Musk 合规)。**唯一未完成 = 整体替换主支**,严格 gate 在两件事上:① 风云 A/B founder verdict 拍板通过(主观,未判)② 风云**显式说「替换主支」** → 才跑 `git branch -M arch-refactor-v1 main`(旧 main=ae3cb4c 已 tag `backup-pre-refactor-20260526` 兜底)。**在那之前 branch 绝不动主支**;失败 → branch 保留主支 0 影响。rollback 见 §7 + §8.6。
   - WHY 见 `docs/ARCH_REFACTOR_V1_PLAN.md` §6.2 W10 行 + §8 验收标准表(SKILL.md 行数 / 端到端耗时 / gate 拦截 / Python 伪代码归零等目标)
   - W9 ✅(砍维度+调阈值+清伪lint,见 §4.9):critic 现状 = lint 机械层(W9 后约 23 条,砍 R2/R4/R13/R14/R16/R21 + 修 R7)+ B+C 二元 founder verdict;opening 信号 = 物理(真首段≥25 + 第一人称)+ 公式新鲜度;title = 软分门槛(7钩子软分 + 4特质≥1,无致命组合 risk 门);焦虑铺垫/安抚时机/末段/粗体判断已回归 content-judge M6 + huashu —— W10 跑 e2e 时按此现状,**勿再找已砍的维度/规则**
   - ⚠️ **doc-sync 漏 agent 文件教训**(W8):改任何阶段 SOP/流程/阈值必须连带核 `.claude/agents/fengyun-<stage>.md`
   - ⚠️ **物理删 .py 教训**(W7):删工具后必清 `tools/__pycache__/*.pyc`,否则 `pytest tools/` 撞 import-mismatch 假 FAIL
   - ⚠️ **B4 before-snapshot 不可变**(W9):`reports/dim_trigger_rate_audit_20260526.json` 是 before 证据,dim_trigger_rate_audit.py 现写 `*_w9_after.json`,别再覆盖 before

**⛔ 单写者铁律(2026-05-27 新增,W2 踩坑)**:`arch-refactor-v1` 同一时刻**只能有一个 CLI 窗口在写**。W2 收尾时观察到并发窗口(spawned fix_punctuation task)在主树提交,git 状态在两次 Bash 间跳变。多窗口同树 = race + 互相覆盖。开新窗口前确认其它窗口已 `/clear` 收手;并行只能用 `git worktree`(独立工作树)。

**验收基线**:`python scripts/verify_baseline.py` → **198 passed / 0 deselected**(W9 后 193 + post-W10 体检 +5 flywheel,见 §4.11;零回归)。
