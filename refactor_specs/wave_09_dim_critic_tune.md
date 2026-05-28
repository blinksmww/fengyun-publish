# Wave 9: 砍维度 + 调阈值 + 清伪 lint(critic 参数数据驱动重校)

> ⚠️ **全程最高风险 wave** —— 改的是 critic 参数/阈值/词典/维度,p-hacking 红线(§8 禁令 #11)。
> **每个阈值/词典/维度改动必须有外部出处**(PHASE1 / corpus 实测 / 论文 / 用户已拍板),写进 commit message。
> **严禁为 ρ/ROC 数字好看挑改动或在 corpus 上 grid search**(memory `feedback_no_p_hacking`)。
> 模式:**你 + verify**;test-first;每维度/每阈值/每规则一 commit;0 改无关业务逻辑。

---

## 0. scope 来源 + 4 个 fork 拍板记录(2026-05-27)

W9 原计划 = ARCH_REFACTOR_V1_PLAN.md §阶段 B(B1-B5):opening 4 维全砍 + title 致命组合 + R13 词典换装 + lint 29→6 RuleFamily。开工先派 explorer ×2 调研现状,发现多个真 fork → AskUserQuestion 集中拍板:

| Fork | 调研发现 | 用户拍板 |
|---|---|---|
| **F1 验收方案** | K-fold-ROC-on-critic **不成立**:W2 删 Track A 数字分,critic 现为 B+C 二元投票(无数字可算 ROC);要砍的 opening/title 维度是**写作侧 harness 信号**(不在 `gate.py` REQUIRED_INVOCATIONS,不卡 ship);「549 条」是 xhs 项目的,本 repo 没有。本 repo 有 `targets.parquet` 2730 篇带 `read_pct` + B4 用的 321 篇 raw 文本。 | **信号分 held-out ρ + 触发率前后**:用本 repo 真数据,parquet proxy(`aid` join)跑 5-fold + held-out 50 的跨账号 Spearman ρ + 触发率前后对比 |
| **F2 lint 价值** | 用户深问「lint 真有用吗,能不能砍 lint」。调研结论(lint-vs-founder-split 铁律):lint 不能整砍(R18-P0/R0/R29/R30/R19 无替补守门),但 R13/R14/R16/R21/R2/R4 是**灵魂判断伪装成机械规则**(无源 + 品味 + 已被 B/C/王小波覆盖)。 | **清伪 lint + 修 R7**:砍 R13/R14/R16/R21/R2/R4(6 条);R5 原样留;R7 删歧义词只留真 AI 味词。原 B3「29→6 RuleFamily」**作废**(给死重换标签还破坏测试,直接砍死重更干净) |
| **F3 R13 词典** | 阈值/severity 有源(花叔 corpus 87.9% 过触发),但换词无源,且 plan 想加的 6 词已在表里。 | **没用就删** → R13 整条砍(并入 F2) |
| **F4 opening 情绪锚点** | ARCH 说砍、B4 审计说调(扩词典,无源);第一人称密度(健康 81.4%)裹在 `_score_emotion_anchor` 同函数里。 | **拆函数**:留第一人称密度,砍情绪锚点动词维 |

**B6 Caveat 守则**:ending 4 维只有 fengyun n=30 样本太小 → **W9 一律不碰 ending**。huashu-only 块(R19-R28,行 240-453)全部来自花叔 99 篇 corpus 实测 + 仍在生产用 → **W9 一律不碰**。

---

## 1. 物理目的(一句话)

把 critic 链路里**永远过/永远不过(零判别力)的维度砍掉、误伤面过大的阈值调松、灵魂判断伪装成机械规则的伪 lint 清掉**,让 lint 回归「无歧义、误判率→0」机械底线,灵魂判断全归 B+C founder verdict —— 每一刀都有 B4 实测命中率 / PHASE1 / lint-vs-founder 铁律出处,**砍的是 0 判别力的死重,不是为了任何指标数字**。

---

## 2. 改动文件清单(精确到行)

### 2.1 `tools/opening_signal.py`(砍 3 维 + 拆 1 维 + 调 1 阈值)

| 动作 | 位置 | 内容 |
|---|---|---|
| 砍 反差感 | `REFRAME_PATTERNS` 52-78 + `_score_reframe` 104-116 | 删函数 + 词典 + `score_opening_signal` 里 `reframe` 计算(368)、dims 项(376)、failed feedback 分支(399-402)、return 项(429) |
| 砍 具体性 | `_score_concreteness` 120-154 | 删函数 + 调用(367)+ dims 项(374)+ feedback(395-398)+ return(427) |
| 砍 信息密度 | `STOPWORDS_CN` 93-101 + `_score_info_density` 188-220 | 删函数 + 词典 + 调用(370)+ dims 项(377)+ feedback(408-412)+ return(430) |
| 拆 情绪锚点 | `EMOTION_ACTION_WORDS` 81-90 + `_score_emotion_anchor` 158-184 | 删函数 + 动词词典 + 调用(369)+ dims 项(376)+ feedback(403-407)+ return(429)。**第一人称密度不动**(已在 `check_physical_constraints` 327-336) |
| 调 真实首段字数 | `MIN_FIRST_PARA_CHARS` 43 + `check_physical_constraints` 317-324 | 阈值 50→25;计算从「整个 intro 块」改为「真·首段」(首个 `\n\s*\n` 分隔块)。第一人称密度 denominator 保持 intro 块不变(不扰动已验证的 81.4%) |
| 留 公式新鲜度 | `OPENING_FORMULA_BUCKETS` / `_score_formula_freshness` 223-296 | **不动**(R28,fy 58.1% 健康) |
| 连带 | docstring 1-30、cli_demo 445-471、`DIM_PASS_THRESHOLD` 注释 | 改「4 维/5 维」→ 实际维数;cli_demo 打印去掉已砍维 |

**post-W9 opening 信号** = 物理约束(真首段≥25 + 第一人称密度≥5)+ 1 个评分维(公式新鲜度≥6)。

### 2.2 `tools/title_signal.py`(砍 1 维 + 调 2 阈值)

| 动作 | 位置 | 内容 |
|---|---|---|
| 砍 致命组合 | `FATAL_ENGLISH_CHARS_THRESHOLD` 58 + `_check_fatal_combo` 227-243 | 删函数 + 阈值常量 + 调用(279)+ 硬 gate(326-328)+ feedback(370-374)+ return 项 `fatal_combo_risk`(388);`english_chars`/`tb_ratio` 降为 advisory 报告项(无 gate)或删(执行时按测试定) |
| 调 7钩子 hard→软分 | verdict 块 334-335 | 删 `elif not hook_type: verdict = "redo"`;`score_hook=20`(315)保留为软分;verdict 仅看 `score_total >= 65` |
| 调 4特质 ≥2→≥1 | feedback 阈值 366 | `len(failed_traits) >= 3`(命中≤1 就 nag)→ `>= 4`(仅命中=0 才 nag),即 ≥1 命中即可接受 |
| 连带 | docstring 11-22、cli_demo 405-431 | 删致命组合数据基础描述 + cli 打印 |

### 2.3 `tools/fengyun_lint.py`(清 6 条伪 lint + 修 R7 词典)

| 动作 | 规则 | 位置 | 出处 / 覆盖 |
|---|---|---|---|
| 砍 | R2 笔者超频 | 564-574 | 15% 阈值纯无源 |
| 砍 | R4 单句双破折号 | 589-599 | R29 已接管破折号总量 |
| 砍 | R13 焦虑铺垫 | 795-828 | 无源 + craft + content-judge M6 覆盖(60% vs M6 70% 打架)|
| 砍 | R14 过早安抚 | 829-847 | 词表仅 6 词 + craft + content-judge M6 覆盖 |
| 砍 | R16 末段悬空 | 849-865 | 15 字阈值无源 + huashu-perspective Step 4 覆盖 |
| 砍 | R21 粗体注水 | 1028-1047 | craft + content-judge D-3 typography 覆盖 |
| 修 | R7 AI 写作味词典 | 682-694 | 删歧义词(强调/证明/增强/凸显/格局 等正常中文,误判率>0)只留真 AI 味词(此外/与此同时/至关重要/深入探讨…)|
| 留 | R5 AI 套话 | 657-669 | 13 词精确,误判率低,机械底线保留 |
| 连带 | 受影响测试 | `test_round26_fixes.py`(实查不断言 R0-R21 主流 rule_id)/ `test_fengyun_lint_huashu.py`(只断言 huashu 块,不受主流砍影响) | 主流砍**预期 0 测试破坏**,执行时复跑确认 |

### 2.4 新建 `tools/w9_signal_validation.py`(F1 验收 harness,test-first)

5-fold + held-out 50 跨账号 Spearman ρ(parquet proxy vs `read_pct`)+ 触发率前后对比。详见 §5。

### 2.5 doc-sync(§8.7 critic 行全套)—— 见 §7

---

## 3. 改前 vs 改后(代码 diff 样例)

### 3.1 opening 真实首段字数(调阈值 + 修计算)

```python
# 改前(check_physical_constraints,317-324):整个 intro 块字数
MIN_FIRST_PARA_CHARS = 50
intro_text = full_opening_text
m = re.search(r"\n##\s", intro_text)
if m:
    intro_text = intro_text[:m.start()]
first_para_chars = len(re.sub(r"\s+", "", intro_text))   # ← intro 块,B4 实测 100% 必过

# 改后:真·首段(首个空行分隔块),阈值 25
MIN_FIRST_PARA_CHARS = 25     # B4: median 真实首段 26 字;≥50 误伤 95.6%
intro_text = full_opening_text
m = re.search(r"\n##\s", intro_text)
if m:
    intro_text = intro_text[:m.start()]
# 真·首段 = intro 块里第一个非空段落(W9 修字段名歧义,见 B6 Caveat)
true_first_para = next((p for p in re.split(r"\n\s*\n", intro_text) if p.strip()), "")
first_para_chars = len(re.sub(r"\s+", "", true_first_para))
# 第一人称密度仍用整个 intro 块(不扰动已验证的 81.4%)
```

### 3.2 title 7钩子 hard gate → 软分

```python
# 改前(326-337)
if fatal_combo["risk"]:
    verdict = "redo"
elif not hook_type:           # ← hard gate,B4 卡掉 72% 卡兹克爆款
    verdict = "redo"
else:
    verdict = "pass" if score_total >= 65 else "redo"

# 改后(致命组合砍 + 7钩子软分)
verdict = "pass" if score_total >= 65 else "redo"
# 注:score_hook(20 分,行 315)保留为软分加权;无钩子的标题靠其它维补分仍可过
```

### 3.3 lint 砍一条(R13 为例,795-828 整块删)

```python
# 改前:# === Rule 13: 深度文焦虑铺垫不足 ===  (795-828,含 anxiety_signals 词表 + <3 阈值 + severity=high)
# 改后:整块删除,不留注释存根(无源 craft,content-judge M6 已覆盖此判断)
#       连带:content-judge SKILL M6 删「R13 violation」引用,改它自己拥有该判断
```

### 3.4 R7 词典修(删歧义词)

```python
# 改前(682-694)AI_WRITING_MARKERS 含正常中文词
[..., "强调", "证明", "增强", "凸显", "格局", "此外", "与此同时", "至关重要", "深入探讨", ...]
# 改后:删 误判率>0 的歧义词,留 真 AI 味词
[..., "此外", "与此同时", "至关重要", "深入探讨", ...]   # 删:强调/证明/增强/凸显/格局
```
> 执行时先 Read 实际词表确认每个词归类,再删 —— 只删「正常中文也高频用」的词。

---

## 4. 外部出处表(每改动一行,无出处不许进 W9)

| # | 改动 | 类型 | 外部出处 |
|---|---|---|---|
| 1 | opening 反差感 `_score_reframe` | 砍 | 花叔 397 篇 4.3% + PHASE1_FACTS L1216-17「不显著」+ B4 6.6%(<5%)|
| 2 | opening 具体性 `_score_concreteness` | 砍 | B4 87.2% 命中(阈值 6 脱钩,>95% 等于没卡)|
| 3 | opening 信息密度 `_score_info_density` | 砍 | B4 100% 命中(算法下界≥10,物理永远过)|
| 4 | opening 首段字数(intro块)→ 真首段≥25 | 砍 broken + 调 | B4 100% 必过(intro 块歧义)+ median 真实首段 26 字,≥50 误伤 95.6% |
| 5 | opening 情绪锚点动词维(拆,留第一人称)| 砍 | B4 调动词词典无源 + F4 用户拍板拆函数;第一人称密度 fy 81.4% 健康(留)|
| 6 | title 致命组合 risk | 砍 | B4 0/321 命中(tb_ratio 用 body_chars=5000 → 永不触发)|
| 7 | title 7钩子 hard→软分 | 调 | B4 全样本 24.6% / 卡兹克爆款仅 28%,hard gate 卡掉 72% 卡兹克爆款 |
| 8 | title 4特质 ≥2→≥1 | 调 | B4 ≥2 仅 3.4% / ≥1 ≈53%(≥2 过严)|
| 9 | R13 焦虑铺垫 | 砍 | 无源 + craft + content-judge M6 覆盖(F3 用户拍板「没用就删」)|
| 10 | R14 过早安抚 | 砍 | 词表 6 词太窄无源 + content-judge M6 覆盖 |
| 11 | R16 末段悬空 | 砍 | 15 字阈值无源 + huashu-perspective Step 4 覆盖 |
| 12 | R21 粗体注水 | 砍 | craft + content-judge D-3 覆盖 |
| 13 | R2 笔者超频 | 砍 | 15% 阈值纯无源(lint-vs-founder「无签名默认删除」)|
| 14 | R4 单句双破折号 | 砍 | R29 已接管破折号总量,R4 边角冗余 |
| 15 | R7 删歧义词 | 修词典 | lint 铁律「误判率→0」:强调/证明/增强/凸显 是正常中文 → 误判率>0,违反机械底线 |

**留(机械核,不动)**:R0/R1/R3/R5/R6/R8/R10/R11/R12/R12b/R17/R18(P0/P1/P2)/R19/R20/R29/R30 + huashu 块 R19-R28。

---

## 5. K-fold + held-out 验收方案(F1 用户拍板)

> ⚠️ **诚实声明**:critic 现为 B+C 二元(无数字分),被砍维度是写作侧 harness 信号。本 repo 唯一可 join `read_pct` 的是 parquet 的**预抽特征(proxy)**,不是信号工具的精确输出。harness 验的是「这些维度瞄准的物理构念跟互动相不相关」(= Round 13 方法论,memory `feedback_data_first_design_loop` 已验证可行),不是「critic ROC」。砍维度的**主证据是零方差(B4 命中率 100%/0%)**,ρ 是佐证。

**数据**:`targets.parquet`(2730,`read_pct`)+ `hook_power_features.parquet`(2723,11 钩子)+ `features.parquet`(2730,50 结构特征),`aid` join。

**proxy 映射**(砍/调维度 → parquet 列):
- 致命组合 → `tb_ratio` + `t_english_chars`(features)
- 真实首段字数 → `b_first_para_chars`(features)
- 7 钩子 → `title_hook_*`(hook_power)
- 第一人称(留)→ `first_para_first_person_open`(hook_power)
- 反差感/情绪锚点(砍)→ `first_para_event_intro`/`first_para_emotional_open`(hook_power proxy)

**harness(`tools/w9_signal_validation.py`,test-first 先写测试)**:
1. **5-fold** `KFold(n_splits=5, shuffle=True, random_state=42)`(沿用 PHASE1 5-fold + xhs critic_v3 KFold(5),有出处)：每个 proxy vs `read_pct` 的 Spearman ρ,报告 5 折 mean ± std。
2. **跨账号 ρ**:按 `account_slug` 分组,要求方向一致性(Round 13 的「≥4/4 同向 + ≥2 显著」标准作参考)。
3. **held-out 50**:固定 seed 随机抽 50 个 `aid` **完全不参与任何折计算/任何阈值检视**,单独报 ρ,跟全样本对比(防过拟合)。
4. **触发率前后**:复用 `dim_trigger_rate_audit.py` 逻辑,在 321 篇 raw corpus 上跑 W9 改动前 vs 后的命中率。

**验收 PASS 标准**:
- (a) 被砍维度的 proxy ρ **不显著为正**(held-out 同向)→ 砍掉不丢真信号 ✅
- (b) 调松阈值的特征,其 ρ 关系**支持新阈值**(如 `b_first_para_chars` 在 25-50 区间不是强正相关)
- (c) **`scripts/verify_baseline.py` 零回归 ≥ 189 passed**(W8 基线)
- (d) 触发率变化**符合 B4 预测**(砍的维度从 gate/dims 链路消失;调的维度命中率往预测方向走)
- (e) held-out 50 ρ 跟全样本一致(无过拟合迹象)

---

## 6. 风险 + 兜底(本 wave 专有)

| 风险 | 兜底 |
|---|---|
| **p-hacking**(为 ρ 挑改动)| 每改动 commit message 写外部出处;砍维度主证据是 B4 零方差**非** ρ;harness 只佐证不挑选;held-out 50 不参与任何调参 |
| 砍维度后某维其实有用 | 几行代码加回来(invariant #4 逆向);git tag `backup-pre-refactor-20260526` 永远可回 |
| 砍 R13/R14 后焦虑判断逃逸 | content-judge M6 接管(本就引用 voice-dna 5.3);doc-sync 把判断改 M6 自己拥有 |
| 砍 R16/R21 后结尾/粗体质量降 | huashu-perspective Step 4 + content-judge D-3 接管(灵魂层质量更高)|
| 改 R7 词典误删真信号词 | 执行时逐词归类,只删「正常中文高频」词;王小波 skill 做长尾兜底 |
| lint 砍破坏测试 | 实查主流 rule_id 无测试断言;每砍一条复跑 `verify_baseline`;huashu 块不碰保 31 测试绿 |
| 第一人称密度受牵连 | 拆 `_score_emotion_anchor` 时第一人称密度留在 `check_physical_constraints`,denominator 不变 |
| doc-sync 漏 agent 文件(W8 教训)| §7 清单含 `.claude/agents/fengyun-critic-*.md` + `fengyun-writer.md` |

---

## 7. doc-sync §8.7 完整连带清单(critic 行最大面)

每砍/改完按这串 grep 旧术语确认无活引用:

- [ ] `WRITE_AGENT.md` Step 4(lint R0-R30 清单 → 改 count + 删砍掉的规则)+ Step 6/6.5(critic 描述不变,核对)
- [ ] fengyun-publish `SKILL.md`(必跑命令骨架 + 工具维数描述)
- [ ] `references/stage_03_verify.md`(**显式 rule 表 24-32 + L91「R0-R30」** → 删砍掉的规则行)
- [ ] `references/frontmatter_checklist.md`(字段计数)
- [ ] `references/failure_modes.md`(失败表)
- [ ] `content-judge/SKILL.md` **M6**(删「R13/R14 violation」lint 引用,改它自己拥有焦虑铺垫/过早安抚判断)+ **D-3**(R21 粗体引用)
- [ ] `fengyun-writer/references/critic_mode.md`(若引用 lint 规则)
- [ ] `tools/verify_audit.py`(若枚举 rule_id)
- [ ] `.claude/agents/fengyun-critic-huashu.md`(**L16「lint(R0-R30)」→ 改 count**)
- [ ] `.claude/agents/fengyun-writer.md`(**L42 信号工具名 + 维数**:opening/title 维度描述同步)
- [ ] `.claude/agents/fengyun-critic-content-judge.md`(若引用 R13/R14/R21)
- [ ] **vendor 镜像** `vendor/skills/fengyun-publish/`(cp -r 同步)+ 若 content-judge/huashu 有 vendor 镜像一并同步
- [ ] 收尾 `grep -rn` 砍掉的 rule_id(R2/R4/R13/R14/R16/R21)全 skill+tools+WRITE_AGENT,确认只剩「已删」标注无活引用

---

## 8. reviewer subagent prompt(全新 session 审稿用)

```
你是 W9(critic 参数数据驱动重校)的 reviewer,全新 session,只读(Read/Grep/Glob)。
审 arch-refactor-v1 分支 W9 的 commit 序列 + refactor_specs/wave_09_dim_critic_tune.md。
binary verdict: SHIP / REVISE。重点(W9 是 p-hacking 红线 wave):
1. 反 p-hacking:每个砍/调/词典改动的 commit message 是否写明外部出处?有没有「为了 ρ/触发率数字好看」挑改动的痕迹?有没有在 corpus 上 grid search?
2. 砍维度:opening 反差/具体/信息/情绪锚点动词维 + title 致命组合是否真从 score 链路移除?第一人称密度(拆函数)是否保留且 denominator 未变?
3. 调阈值:真首段 50→25 + 真·首段计算修了字段名歧义?7钩子 hard gate 真删?4特质 ≥2→≥1?
4. 清 lint:R2/R4/R13/R14/R16/R21 整块删干净?R7 只删歧义词没动真信号?R5 + 机械核(R0/R18/R29/R30/R19)+ huashu 块**未动**?
5. doc-sync:§7 清单全过?尤其 content-judge M6 删 R13/R14 引用改自己拥有 + agent 文件 L16/L42 + vendor 镜像?(W8 教训:agent 文件最易漏)
6. 0 改无关业务逻辑;harness `w9_signal_validation.py` test-first;held-out 50 不参与调参。
7. 验收:verify_baseline ≥189 零回归?harness 报告砍维度 proxy ρ 不显著为正 + held-out 一致?
逐条给证据(file:line),任一 P0 → REVISE。
```
