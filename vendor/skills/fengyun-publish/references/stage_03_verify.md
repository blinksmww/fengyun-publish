# Stage 3 Verify — 详细 SOP

> 主体跳转:`SKILL.md` Stage 3 / 4 · Verify
> 跨阶段约束:见主体「关键不变量」段(R18 红线是硬否决 / image_paths 非空 / 双轨真 invoke / writer 真 invoke)
> 本文件来源:SKILL.md.pre-w1-bak L555-1010,W1 纯拆分不改字段
>
> **⚠️ W4(2026-05-27)**:`lint_pass`/`wangxiaobo_*`/`critic_b_*`/`critic_c_*`/`critic_vote_pass`/`force_ship` 已迁 invocation log。
> 双轨 critic 各写 `critic_b_huashu.invocation.json` / `critic_c_content_judge.invocation.json`(`--input-file` = 当前 draft);
> 主线程跑 critic_vote 后写 `verify.invocation.json`(`--result ship|force_ship|revise`)。
> gate 查这些 invocation + `input_hash` 匹配当前稿。下文 frontmatter pass_flag 写法是 W4 前历史描述 —— 以本 banner + `frontmatter_checklist.md` 为准。

---

## Step 4 · 机械 lint(必跑直到 0 violation)

```
python tools/fengyun_lint.py output/drafts/YYYYMMDD-<slug>-v0.md
```

读 JSON 输出 `output/drafts/YYYYMMDD-<slug>-v0.lint.json`,按规则处理:

| violation | 修复方式 |
|---|---|
| **R0_halfwidth_punctuation** | 直接跑 `python tools/fix_punctuation.py <draft>`,会半角→全角并写回原文件 |
| **R12_word_count_too_short**(<4000 字)| 回 Step 3 让 fengyun-writer 扩写,扩到 ≥ 4000 |
| **R12_word_count_too_long**(>5000 字)| 让 fengyun-writer 精简(优先砍重复论证 / 段尾悬空) |
| **R1_brackets / R3_excl / R5_buzzwords / R6_kazik / R7_ai_markers / R8_anxiety / R17_english_like** | 用 Edit 工具按 lint 给的 fix 字段逐条改(W9 砍 R4_dash;R29 已接管破折号总量)|
| **R10_no_chapters**(无 H2/H3)| Edit 加 3-5 个章节标题 |
| **R11_too_fragmented** | 回 fengyun-writer 改稿,告诉它 lint 报告(**W9 砍 R13/R14/R16/R2/R21 伪 lint** — 焦虑铺垫/安抚时机/末段/粗体 craft 判断回归 content-judge + huashu founder verdict)|
| **R18_P0_self_as_ai** ⛔(明确自指 AI 身份)| **删或重写命中段**(全自动:lint matches 给了具体 ctx,机械可定位)。回 fengyun-writer 改稿删段;改到天花板仍 P0 → critic_vote 判 `aborted_r18` 自动终止(不 ship,无人工)|
| **R18_P1_architecture_leak** ⚠️(架构 / skill / 工具栈暴露)| 不阻断 ship 但 writer 必须改。回 fengyun-writer 改稿。`r18_dashboard.py` 周报会告警是否需修 L1 writer |
| **R18_P2_automation_leak** 💭(自动化流程暴露)| 改稿删自动化提及。`r18_dashboard.py` 计入触发率统计 |

改完**重跑 lint**,循环到 `n_violations == 0` → `lint_pass`。两条出口分清(优先级:high 阻断 > partial):
- **只剩 low/medium 警告**(非阻断级)→ `lint_partial_pass: true`(带 degraded,继续 Step 5)
- **high severity 改 3 轮还在**(R12 字数振荡等结构性写不出)→ 自动终止 + ERROR 日志(writer deeper issue,cron 下轮选别的主题),**无人工**

##### → 立即写入 frontmatter(Step 4 完成后)

```yaml
lint_pass: true
# 或只剩 low/medium 警告走兜底:
# lint_partial_pass: true
```

1 个字段。写完才进 Step 5。

> **W2.C2 注**:原「Step 4.5 humanizer-zh 去 AI 味」整段(49 行)已删除(2026-05-27)。
> 调研发现 humanizer-zh 在 11 篇 v0 全 pass 但破折号实际 9/篇(vs kazik 真稿 0.2/篇,
> 45× 差异)= 自我汇报无外部验证。改为在 fengyun_lint 直接加 R29(破折号 ≤ 3/篇)+
> R30(否定式排比 ≤ 2/篇)硬约束,阈值用调研 agent 实测 kazik corpus 数据。
> invariant #4 「0 消费者 = 0 生产」落地。

## Step 5 · 语感预审(王小波 perspective)

invoke `wangxiaobo-perspective` skill,把当前 draft 喂进去:

```
用 wangxiaobo-perspective 审视 output/drafts/YYYYMMDD-<slug>-v0.md,
重点找翻译腔 / 英式中文 / 「不是想出来的是翻译过来的」表达。
输出每条带:位置 + 母语建议。
```

应用王小波给的建议(Edit),改完**重跑 fengyun_lint 确认没破坏其他规则**。

**⛔ Round 21 P0-9 fake-pass 防伪铁律**:
- frontmatter `wangxiaobo_pass: true` 时,**必须**同时写 `wangxiaobo_real_run: true` + `wangxiaobo_source: "wangxiaobo-perspective skill, found N translation-tone hits"`
- gate.py 看到 `wangxiaobo_pass: true` 但缺这两个字段 → 当场阻断 ship
- 主线程不许「自己读一遍觉得没翻译腔直接标 pass」— 必须真 invoke wangxiaobo-perspective skill

### 失败回退

- wangxiaobo-perspective skill **不存在**(invoke 报 "skill not found" / 文件 404)→ 跳过 Step 5,记 `degraded.wangxiaobo = "skill_missing"`,继续 Step 6。
- wangxiaobo-perspective skill **存在但执行出错**(timeout / crash / 返回异常)→ 标记 `degraded.wangxiaobo = "invoke_error:<reason>"` 但**仍然继续 Step 6**,不阻断。
- ⛔ **不许因为「测试简化」/「省时间」/「觉得没必要」跳过**。只有真不存在或真报错才允许 skip。

##### → 立即写入 frontmatter(Step 5 完成后)

```yaml
wangxiaobo_pass: true
wangxiaobo_real_run: true
wangxiaobo_source: "wangxiaobo-perspective skill, found N translation-tone hits"
```

3 个字段。只有王小波真跑了才写 `wangxiaobo_pass: true`。写完才进 Step 6。

## Step 6 · critic 双轨 vote(W2.C6 双轨全自动版,2026-05-27)

> **W2.C6 架构变更**:删 Track A(score_draft.py 数字分,用户决策「彻底删」)。
> 质量底线从「A ≥ 60 数字分」迁移到 **lint(机械层,W9 后约 23 条:砍 R2/R4/R13/R14/R16/R21 伪 lint)+ B+C 双轨灵魂共识**。
> 双轨对等(删「C 硬否决」特殊命名):B、C 任一拒绝都 revise,不分谁。
> 全自动闭环(删 human_gate / partial_pass / auto_abort)。

双轨并行调用,任何一轨拿不到都按降级表降级。

**⛔ fake-pass 防伪铁律(critic_vote_pass=true 时必查):**
- `critic_b_real_run: true` + `critic_b_source: "huashu-perspective skill, ship verdict, ..."` — 必须真 invoke huashu-perspective skill
- `critic_c_real_run: true` + `critic_c_source: "content-judge skill, 挂名意愿 yes, ..."` — 必须真 invoke **content-judge** skill(Round 9 蒸馏的风云本人 decision-time skill,不是 fengyun-writer critic_mode)
- gate.py 任一缺失 → 当场阻断 ship
- **审计实证**(2026-05-25 trapdoor 文):主线程之前的 verdict 都是「拍脑袋写 ship 没真调 skill」,防伪上线后当场抓出

### Track B · huashu-perspective(emotion-judgement,binary)

- 若 `C:\Users\23303\.claude\skills\huashu-perspective\SKILL.md` **存在**:
  ```
  用 huashu-perspective 评 output/drafts/YYYYMMDD-<slug>-v0.md,
  输出:ship / 不 ship 的 binary 判断 + 「哪一段没灵魂」具体位置(一段一句话)。
  不要给数字,只要 binary + 原因。严格按你的品味判断,该 reject 就 reject。
  ```
- 若不存在 → **B 轨缺席**,记 `degraded.B = "skill not installed"`

### Track C · content-judge skill(founder voice,binary)— Round 9 蒸馏 + Round 18 lock

- **主路径**:`~/.claude/skills/content-judge/SKILL.md`(2026-05-24 蒸馏,decision-time perspective skill)
  ```
  用 content-judge 评 output/drafts/YYYYMMDD-<slug>-v0.md,
  输出:风云愿不愿意挂名(binary,yes / no) + 改稿点(具体到段落)。
  严格按风云本人 voice 判断,不像本人写的就 no。
  ```
- **降级路径**:若 content-judge 不存在 → 回 `~/.claude/skills/fengyun-writer/references/critic_mode.md`
- 都不存在 → **C 轨缺席**,记 `degraded.C = "content-judge missing"`

> ⛔ **评委 prompt 铁律**:B / C 的 invoke prompt **永远保持「严格审核」语气,绝不透露任何「改稿轮次」「上限」「最后一轮」信息**。评委只管按品味判 ship/reject,不知道 harness 有几轮。轮次裁决全在 `critic_vote.py` 代码层,评委不可见。

**content-judge 是什么**:Round 9 用 huashu-nuwa 蒸馏的风云本人 decision-time skill,decision_mode 工作流替风云在 ship pipeline 各 gate 自动回答(dogfood / 改稿方向 / 选题胆量)。Critic mode 是其中副产物。

### 投票规则(总闸 — 评委视角)

把双轨结果丢给 `tools/critic_vote.py`(或 Claude 自己按下表判):

| B(ship)| C(挂名)| 决议 |
|---|---|---|
| ✅ ship | ✅ 挂名 | **进 Step 7**(双轨共识过)|
| ✅ ship | ❌ 不挂名 | **revise**(任一票否决,对等)|
| ❌ reject | ✅ 挂名 | **revise**(任一票否决,对等)|
| ❌ reject | ❌ 不挂名 | **revise** |

降级模式:

| 缺失轨 | 决议规则 |
|---|---|
| 只 B 缺 | 听 C:C 挂名 → 进 Step 7;C 不挂名 → revise。记 `degraded.B` |
| 只 C 缺 | 听 B:B ship → 进 Step 7;B reject → revise。记 `degraded.C` |
| B 和 C 都缺 | **revise**(无灵魂层底线,改稿重试,不放行)。记 `degraded.B + degraded.C` |

⛔ **R18-P0 全自动处理**:末轮 lint 命中 **R18-P0(明确自指 AI 身份 = 商业机密泄漏)**→ **跳过 force_ship**(机密泄漏绝不强推)。未到天花板 → revise 自动删段(lint 给了具体 ctx);改到天花板仍 P0 → `aborted_r18` 自动终止(ERROR 日志,不 ship 自爆稿,**无人工**)。R18-P1 / P2 不阻断 ship,按 revise 正常走 gate tree。

> ⛔ **不许直接停在「revise」决议上**。投票判定 `revise` 必须进 Step 6.5 跑改稿循环。`critic_vote.py --all-rounds` 内部裁决轮次(代码层),你只管:它返回 `revise` 就继续改,返回 `ship`(含 `force_ship`)就进 Step 7,返回 `aborted_r18`(改到天花板仍自爆 AI,自动终止不 ship)就停。**全程无人工交互**:`aborted_r18` 不是「甩人工」,是自动终止 + ERROR 日志,cron 下轮选别的主题。**轮次上限是代码层隐藏机制,绝不写进任何评委 prompt,也不要在改稿时告诉自己「就剩几轮了」而放水**。这是 harness 的灵魂 —— retry loop + 全自动闭环。

##### → 立即写入 frontmatter(Step 6 投票完成后)

```yaml
# B 轨
critic_b_real_run: true
critic_b_source: "huashu-perspective skill, ship verdict, 第3段emotion_missing"

# C 轨
critic_c_real_run: true
critic_c_source: "content-judge skill, 挂名意愿 yes, 改稿点: 第5段voice_drift"

# 投票结果(根据 critic_vote.py decision 写一个)
critic_vote_pass: true
# 或: revise_loop_pass: true   (改稿后双过)
# 或: force_ship: true         (3 轮改稿后仍未双过,代码层隐藏天花板强制 ship)
```

5 个字段(双轨各 2 + 决议 1)。写完才进 Step 6.5 或 Step 7。

> **force_ship 说明**:critic_vote.py 返回 `force_ship: true` 时,frontmatter + run log 都写 `force_ship: true`,日志 WARN 标记。这是数据飞轮信号(统计强制 ship 比例),不是失败 —— Real Artists Ship,全自动闭环不卡死。

## Step 6.5 · critic-revise loop ⛔ BLOCKING(改稿循环)

**触发条件**:Step 6 投票规则判定「**回 Step 3 改稿**」(decision = `revise`)。
**这是 harness 的灵魂**,不许跳过、不许偷懒、不许把 critic 反馈丢掉直接停。

> **注意**:「回 Step 3」是投票表里的措辞,实际执行走的是本 Step 6.5 子循环——**不是完全重写全文**,不是从 Step 3 重头来。6.5 是嵌在 Step 6 和 Step 7 之间的局部修复子循环,只改 critic 指出的段落(±10%),然后走精简版 4→5→6,再投票。外层流程不回头。

执行流程必须**严格按这个 7 步序列**,不许跳过任何一步:

### 6.5.1 · 收集双轨 critic 的具体改稿点

| 轨 | 收集什么 |
|---|---|
| **B 轨**(huashu)| 「不 ship」对应的具体段落编号 + 原因类型:`voice_drift / 缺_lived_stake / 鸡汤 / emotion_missing / 选题胆量不足` |
| **C 轨**(content-judge)| 「不挂名」对应的具体段落 + 改稿建议(必须落到段落,不许说"整体感觉") |

任一轨缺席(skip / degraded)→ 该轨跳过收集,不视为 fail。

### 6.5.2 · 拼 revise_brief.md 喂给 fengyun-writer

**文件位置**:`output/drafts/<slug>-revise-brief-r{N}.md`(N = 改稿轮次,r1 / r2)

**必含字段**:

```markdown
# Revise Brief · {slug} · Round {N}
*生成时间:{ts} · 自动 by fengyun-publish Step 6.5*

## 当前 draft
{当前 draft 路径,如 output/drafts/<slug>-v{N-1}.md}

## 双轨 verdict 原文
### B 轨 (huashu)
verdict: 不 ship
具体段落 + 原因:
- 第 X 段: {段落引文} → {原因类型}
- ...

### C 轨 (content-judge)
verdict: 不挂名
具体段落 + 改稿建议:
- 第 X 段: {段落引文} → {建议}
- ...

## 优先修复点(merge 双轨 top 3)
1. {段落} : {改稿动作}
2. ...
3. ...

## 改稿硬约束(⛔ writer 必读)
1. **总字数变动 ≤ ±10%**(原文 X 字 → 目标区间 [X*0.9, X*1.1])。避免大改重写丢 voice
2. **必须保留**原有北极星(`{北极星}`)+ 章节结构(章节标题不许改)
3. **只针对 critic 指出的具体段落改**,其它段落不动
4. **改稿动作类型**(按 critic 反馈选):加 lived stake(作者第一人称体验)/ 删鸡汤 / 补 emotion / 补 stake / 补押注表态
5. **voice 一致性**:fengyun-writer Step 0(voice-dna.md)必读不跳过
```

### 6.5.3 · 调用 fengyun-writer skill 改稿模式

**触发语**(必须按这个格式写,fengyun-writer 才会进改稿模式而不是从头写):

```
用 fengyun-writer 按 output/drafts/<slug>-revise-brief-r{N}.md 改稿,
输入 draft = output/drafts/<slug>-v{N-1}.md,
输出 draft = output/drafts/<slug>-v{N}.md。

约束:
- 不重新写,只针对 revise_brief.md「优先修复点」列出的段落改
- 总字数变动 ≤ ±10%
- 章节结构 + 北极星 + 标题不许改
- 保留 voice 一致性(Step 0 必读)
```

fengyun-writer 改完输出新 draft v{N}。

### 6.5.4 · 改完立刻回 Step 4 lint(必须 0 violation)

```
python tools/fengyun_lint.py output/drafts/<slug>-v{N}.md
```

有 violation → 按 Step 4 表修,改完重跑直到 0。

### 6.5.5 · 回 Step 5 王小波语感预审

invoke `wangxiaobo-perspective`,确认改稿没引入新的翻译腔。

**跑/跳条件**:
- 改稿有**新增文字 ≥ 50 字** → **必跑**(填补段落最容易产生翻译腔)
- 纯删减改稿(只删句子,新增文字 < 50 字) → 可跳过,记 `run log` 的 `degraded` 字段:`wangxiaobo = "skipped: pure deletion"`

### 6.5.6 · 回 Step 6 重跑双轨 critic

| 轨 | 命令 |
|---|---|
| B | invoke `huashu-perspective` 评新 draft(prompt 保持严格,不提轮次)|
| C | invoke `content-judge` 评新 draft(prompt 保持严格,不提轮次)|

跑完拿到两个新 verdict。⛔ **绝不在评委 prompt 里写「第几轮」「最后一次」「上限」** —— 评委永远天真严格。

### 6.5.7 · 双轨门控树投票(W2.C6 双轨全自动版,2026-05-27)

把双轨 verdict 累积成 rounds.json,丢给 `critic_vote.py --all-rounds`,它返回 decision(代码层 `gate_tree` + 隐藏天花板):

| 条件 | 决议 | 动作 |
|---|---|---|
| B ship + C ship | `ship` | 进 Step 7(封面) |
| 单轨 ship + 另一轨 skip | `ship` | 听 ship 轨,记 degraded,进 Step 7 |
| 任一轨 reject(对等,不分谁) | `revise` | 回 Step 6.5 改稿 |
| B skip + C skip | `revise` | 无灵魂底线,改稿重试(不 abort) |
| + revise & 未到天花板 | — | 重复 Step 6.5(改稿轮次 +1) |
| + revise & 到隐藏天花板 | `ship` + `force_ship` | 强制 ship + WARN 标记(代码层裁决,见下)|
| 末轮 lint 含 **R18-P0** + 未到天花板 | `revise` | 自动删段修(lint 可定位 ctx)|
| 末轮 lint 含 **R18-P0** + 到天花板 | `aborted_r18` | ⛔ 跳过 force_ship,自动终止(ERROR 日志,不 ship,无人工)|
| 任一轮 lint 含 R18-P1 / P2 | 不阻断 | 走 gate tree;`r18_dashboard.py` 计入触发率统计 |

**核心原则**(W2.C6):
- 双轨**对等**:B、C 任一 reject 都 revise,删「C 硬否决」特殊命名
- 全自动闭环:删 human_gate / partial_pass / auto_abort,没有真人裁决出口(R18-P0 除外)
- **轮次天花板是代码层隐藏机制**(`critic_vote.py` 常量 `REVISE_CEILING`),你只看 decision,不要把轮次信息透露给评委或拿来给自己放水

### 6.5.8 · 隐藏式天花板 force_ship(W2.C6 全自动闭环,2026-05-27)⛔ 代码层裁决

> **W2.C6 重写**:删 human_gate / partial_pass / auto_abort / D-2 代答 / 推荐版本算法。
> 全自动闭环 —— 没有真人裁决出口(唯一例外 R18-P0)。

**机制(代码层,LLM 不可见)**:每轮改完把累积 rounds 丢给 `critic_vote.py --all-rounds`。它内部有隐藏轮次天花板常量 `REVISE_CEILING`:

- 未到天花板 + 末轮 revise → 返回 `decision: revise`,继续 Step 6.5 改稿
- **到天花板仍未双过 → 返回 `decision: ship` + `force_ship: true`**(强制 ship,WARN 日志)

**执行流程**:

1. 累积每轮 verdict + lint 路径成 rounds.json:

```json
{
  "rounds": [
    {"round": 1, "draft_path": "output/drafts/<slug>-v0.md",
     "b_verdict": "no-ship", "c_verdict": "ship",
     "lint_json_path": "output/drafts/<slug>-v0.lint.json"},
    {"round": 2, "draft_path": "...-v1.md", "b_verdict": "no-ship", "c_verdict": "ship",
     "lint_json_path": "...-v1.lint.json"},
    {"round": 3, "draft_path": "...-v2.md", "b_verdict": "no-ship", "c_verdict": "ship",
     "lint_json_path": "...-v2.lint.json"}
  ]
}
```

2. 跑:
```bash
python tools/critic_vote.py --all-rounds <rounds.json> \
    --out output/runs/<slug>-vote.json
```

3. 读 `decision` 字段,**全自动执行**(连点击都不要):
   - `ship`(无 force_ship)→ 双轨共识过,进 Step 7,写 `critic_vote_pass: true`
   - `ship` + `force_ship: true` → 隐藏天花板强制 ship,进 Step 7,写 `force_ship: true` + WARN
   - `revise` → 回 Step 6.5 改下一轮(评委不知有上限,你也不要透露)
   - `aborted_r18` → 跳过 Step 7,自动终止 pipeline + ERROR 日志(改到天花板仍自爆 AI,不 ship,**无人工**;cron 下轮选别的主题)

⛔ **绝不**:① 把 `REVISE_CEILING` 数字写进任何评委 prompt ② 因为「快到上限了」给改稿放水 ③ 在评委 prompt 里说「这是最后一次」。评委永远天真严格,天花板只在 critic_vote.py 代码里。

**force_ship 是数据飞轮信号**:frontmatter + run log 写 `force_ship: true`,日志 WARN。W3 再加真通知;现在先靠日志统计「强制 ship 比例」回填校准(比例过高 = writer 或评委阈值要调)。

**Step 9 报告必加字段**(force_ship 时):
- `decision: ship` + `force_ship: true`
- `force_ship_reason: "N 轮改稿后 B/C 仍未双过,隐藏天花板强制 ship"`
- 末轮 round_info 对照表(round / b_verdict / c_verdict)

### 6.5 铁律 ⛔

- 不许跳过任何小步骤(6.5.1 → 6.5.7,必要时 6.5.8)
- 改稿不许大改重写(±10% 字数硬约束)
- 改稿到隐藏天花板 → critic_vote.py 自动 force_ship(全自动闭环,不卡死,不甩人工;但 R18-P0 是例外,自动终止 aborted_r18)
- critic 反馈必须落到具体段落,不许说"整体感觉不行"
- voice 一致性优先于其它一切修复
- **评委永远天真严格**:B/C prompt 绝不出现「轮次」「上限」「最后一次」字样
- **R18-P0 也全自动**:revise 自动删段;改到天花板仍 P0 → aborted_r18 自动终止(ERROR 日志,不 ship 自爆稿,**无人工**)。force_ship 不适用(机密红线优先)。**全流程零人工 gate**,唯一人工动作是 pipeline 外的草稿箱审阅 + 点发出
