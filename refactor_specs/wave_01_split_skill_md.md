# W1 spec: 拆 SKILL.md 1480 → ≤ 300 主体 + 6 references/

> **wave**:W1
> **状态**:🚧 in-progress
> **subagent 已用**:explorer `a416e07e87ce1f343`(完工)
> **subagent 待用**:verify / reviewer / Musk 监督员(本 wave 收尾派)
> **基线**:`46e9e21`(W0.2 完工状态)

---

## 1. 物理目的(一句话)

把 `~/.claude/skills/fengyun-publish/SKILL.md` 当前 **1446 行**(explorer 实测,不是 1480 — outline 验证后修正)拆成 **主体 ≤ 300 行 thin orchestrator** + **6 个 `references/` 子文档**,治 Lost-in-Middle(arxiv 2307.03172 中段信息掉 30%+),让 Claude 主线程读 SKILL.md 时不再迷失。

**W1 是纯拆分** — **切位置不动内容**。删冗余 / 改双轨 / 删 humanizer-zh 等都留给 W2 W6 W9。

---

## 2. 改动文件清单

### 2.1 改动的 1 个文件

| 文件 | 改动 |
|---|---|
| `C:\Users\23303\.claude\skills\fengyun-publish\SKILL.md` | 1446 行 → ≤ 300 行,内容迁出到 references/ |

### 2.2 新建的 6 个 references/ 文件

| 文件 | 来源(SKILL.md 行号) | 预估行数 |
|---|---|---|
| `references/stage_01_collect.md` | L60-292(Step 1.0 + 1.1-1.3 + 1.5 dogfood)+ L294-346(Step 2) | ~180 |
| `references/stage_02_write.md` | L348-369(Step 3)+ L372-461(Step 3.3)+ L463-553(Step 3.5) | ~130 |
| `references/stage_03_verify.md` | L555-585(Step 4)+ L587-635(Step 4.5)+ L637-668(Step 5)+ L670-763(Step 6)+ L765-1010(Step 6.5) | ~250 |
| `references/stage_04_publish.md` | L1011-1255(Step 7 + 7.1-7.3)+ L1257-1318(Step 8)+ L1320-1369(Step 9) | ~150 |
| `references/failure_modes.md` | L1373-1389(降级总表)+ L1414-1423(配套脚本)+ L1438-1445(调试 hook) | ~80 |
| `references/frontmatter_checklist.md` | 9 处「→ 立即写入 frontmatter」合并(L360-368 / L453-461 / L546-552 / L578-584 / L627-635 / L660-668 / L741-762 / L1127-1134 / L1195-1207) | ~60 |

**总迁出**:~850 行,加 references/ 各自的标题/锚点/跳转 SKILL.md 元行 → 实际 ~850-950 行。

### 2.3 主体 SKILL.md ≤ 300 行 12 块构成

| # | 块 | 来源 | 预估行 |
|---|---|---|---|
| 1 | Frontmatter | L1-4 维持 + 微调 description | 5 |
| 2 | H1 + tagline | 新写 | 3 |
| 3 | Overview / When to use(触发 + 反触发) | L8-30 合并精简 | 25 |
| 4 | **关键不变量(首部一份)** | L32-39 + L1425-1432 + R18/image_paths/north_star 合并 | 30 |
| 5 | **4 阶段流程一览**(每阶段 1 H2 + 3-4 行说明 + bash 真命令骨架 + 跳转 references/) | 9 步重整 4 阶段 | 60 |
| 6 | 关键路径 + 配置 | L41-50 精简 | 12 |
| 7 | 失败行为概览(跳 failure_modes.md) | L1373-1389 概览版 | 15 |
| 8 | Output Format | L1320-1369 精简 | 20 |
| 9 | References(跳转 6 个文件) | 新写 | 10 |
| 10 | **关键不变量(尾部一份,首尾各一份防 Lost in Middle)** | 块 4 复述 | 15 |
| 11 | 风云手动只做的一件事(收尾点睛) | L1434-1436 | 3 |
| 12 | 章节间隔 / 空行 | — | ~30 |

**合计**:**228 行**(留 ~70 行预算给 W2-W9 后续调整)。

---

## 3. 改前 vs 改后(对照样例)

### 改前(SKILL.md L60-123 Step 1.0,1900 字 Python 伪代码)

```markdown
#### Step 1.0(新)ITI 架构数据驱动候选排序

**Round 12 升级 2026-05-24**:从 aihot 单源升级到 **ITI 第一段聚合**...

```python
from tools.iti_collect import collect_pool          # I-1 广搜(NEW Round 12)
from tools.topic_recommender import rank_aihot_candidates  # T 选题
from tools.event_dedup import check_event_dedup     # T 去重

# 1a. I-1 Python 信源:Python 脚本能调的 5 个源
pool_result = collect_pool(hours=24)
...
```

**降级路径**(I-1 失败时):
- 6 信源全失败 → fallback 到原 aihot 单源调用
...
```

### 改后(SKILL.md 主体只剩 4 阶段一览的 Stage Collect 12 行)

```markdown
## Stage 1 / 4 · Collect(选题 + 调研)

ITI 三段漏斗(I-1 广搜 → T 选题 → I-2 深搜),输出 `output/research/<slug>.md`。

**必跑命令**:
- `python tools/iti_collect.py --hours 24 --out output/runs/<slug>/iti_pool.json`
- `python tools/topic_recommender.py --pool output/runs/<slug>/iti_pool.json`
- `python tools/iti_explore.py <slug> --entities ... --main-source-urls ...`

详见 `references/stage_01_collect.md`(含 ITI 三段实现、dogfood gate harness、降级路径)。
```

### 改后(references/stage_01_collect.md 内容 — L60-292 原内容迁过来,不改字)

```markdown
# Stage 1 Collect — 详细 SOP

> 主体跳转:`SKILL.md` Stage 1 / 4

## Step 1.0 ITI 架构数据驱动候选排序

(原 SKILL.md L60-123 内容,1 字不改)

## Step 1.1 抽核心事件

(原 SKILL.md L125-133 内容)

...
```

---

## 4. 执行步骤(主线程严格按顺序)

### Step 1:备份当前 SKILL.md(必做,Newton 「先备份再全上」)

```bash
cp ~/.claude/skills/fengyun-publish/SKILL.md ~/.claude/skills/fengyun-publish/SKILL.md.pre-w1-bak
```

### Step 2:创建 references/ 目录

```bash
mkdir -p ~/.claude/skills/fengyun-publish/references
```

### Step 3:按 §2.2 表逐个新建 references/ 子文档

**6 个文件,主线程单 agent 串行写,不 fan-out**(W1 关键 wave 不允许 fan-out,§8 禁令 #9)。

每个文件按下面模板:

```markdown
# Stage X <name> — 详细 SOP

> 主体跳转:`SKILL.md` Stage X / 4
> 跨阶段约束:见主体「关键不变量」段(R18 / image_paths / north_star)

## (从 SKILL.md 原内容粘贴,不改字)
```

**粘贴时严格执行**:
- ⛔ 不删任何内容(humanizer / System A-B / 三轨 critic / 5 perspective 引用 全保留)
- ⛔ 不改任何字段(`writer_pass: true` 不改名)
- ⛔ 不合并段落(原来分散的「→ 立即写入 frontmatter」9 处先各自迁,W1 不合并到 checklist;W1 末 grep 验证全活后再合并)
- ✅ **只改内部 link**:`Step X.X` 引用改成 `references/stage_0Y_*.md#step-X-X`(W1 末 grep 验证)

### Step 4:重写 SKILL.md 主体(≤ 300 行 12 块结构)

按 §2.3 的 12 块结构,**新写主体**(不是粘贴原文)。
- 块 1 Frontmatter 维持
- 块 2-11 按预估行数新写,严格 ≤ 300 行

**主体里禁止出现**:
- ⛔ Python 伪代码块(改成 bash 真命令骨架)
- ⛔ 9 处分散的「→ 立即写入 frontmatter」(整体跳转 `references/frontmatter_checklist.md`)
- ⛔ 任何 > 5 行的实现细节(都跳 references/)

### Step 5:跨章节 link 校验

```bash
# grep 找所有 "Step \d" 内部引用
grep -nE "Step [0-9]" ~/.claude/skills/fengyun-publish/SKILL.md
grep -nE "Step [0-9]" ~/.claude/skills/fengyun-publish/references/*.md

# 验证每条 "详见 references/X" 的 X 文件真存在
grep -oE "references/[a-z_0-9]+\.md" ~/.claude/skills/fengyun-publish/SKILL.md | sort -u
ls ~/.claude/skills/fengyun-publish/references/
```

期望:主体 SKILL.md 里所有 link 都活,无悬空跳转。

### Step 6:行数验证

```bash
wc -l ~/.claude/skills/fengyun-publish/SKILL.md
wc -l ~/.claude/skills/fengyun-publish/references/*.md
```

期望:
- SKILL.md ≤ 300
- references/ 6 个文件,总和 ≤ 950

---

## 5. 验收命令(W1 专有,verify subagent 跑)

### 5.1 通用基线(每 wave 必跑)

```bash
python scripts/verify_baseline.py
```

期望:112 passed / 6 deselected / lint 5 篇无 crash(W0 baseline 不变)。

### 5.2 W1 专有验收

```bash
# 1. 主体行数验证
SKILL_LINES=$(wc -l < ~/.claude/skills/fengyun-publish/SKILL.md)
test "$SKILL_LINES" -le 300 || echo "FAIL: SKILL.md $SKILL_LINES > 300"

# 2. references/ 文件数验证
REF_COUNT=$(ls ~/.claude/skills/fengyun-publish/references/*.md 2>/dev/null | wc -l)
test "$REF_COUNT" -eq 6 || echo "FAIL: references/ has $REF_COUNT files, expect 6"

# 3. 跨章节 link 全活(SKILL.md 里跳转的 references/ 文件都存在)
for f in $(grep -oE "references/[a-z_0-9]+\.md" ~/.claude/skills/fengyun-publish/SKILL.md | sort -u); do
  test -f "~/.claude/skills/fengyun-publish/$f" || echo "FAIL: $f not exists"
done

# 4. 备份文件还在(rollback 路径)
test -f ~/.claude/skills/fengyun-publish/SKILL.md.pre-w1-bak || echo "FAIL: backup missing"

# 5. 内容一致性:迁出去的内容没丢字(diff 法)
# 把 SKILL.md + references/*.md 拼起来跟备份的 SKILL.md.pre-w1-bak 比 — 字数应大致相等(± 5%)
ORIG_WORDS=$(wc -w < ~/.claude/skills/fengyun-publish/SKILL.md.pre-w1-bak)
NEW_WORDS=$(cat ~/.claude/skills/fengyun-publish/SKILL.md ~/.claude/skills/fengyun-publish/references/*.md | wc -w)
# 期望 NEW_WORDS / ORIG_WORDS in [0.95, 1.15](允许新写的主体多一些标题/跳转)
```

---

## 6. 风险 + 兜底(W1 专有,基于 explorer §5)

### 6.1 跨章节 link 漏改

**风险**:Step 6.5 内 `回 Step 4 lint` / `回 Step 5 王小波` / `回 Step 6 重跑三轨` 等 ~10 处内部 link 漏改路径。

**兜底**:Step 5 全文 grep `Step \d` 校验,逐条改成新路径。reviewer subagent 收尾再 grep 一遍。

### 6.2 关键不变量分散

**风险**:R18 / image_paths / north_star 当前分散在 8+ 处,主体「关键不变量」段如果只列 R18 没列其他两个会丢约束。

**兜底**:块 4 + 块 10 各列 3 条铁律(R18 ⛔ / image_paths 非空 ⛔ / north_star 必填 ⛔),首尾各一份。references/ 各文件内的提及保留,但不再重新定义铁律(只描述触发位置)。

### 6.3 W1 越界改内容(误删 humanizer 等)

**风险**:主线程在拆分时手痒删了 W2 计划砍的死代码。

**兜底**:
1. reviewer subagent 在审 W1 commit 时,**diff 应该只有「位置变化」**,任何「删段落」「改字段」「合并表格」视为越界
2. SKILL.md.pre-w1-bak 备份保留;wave 末跑 word count diff(§5.2 #5)验证

### 6.4 主体超 300 行

**风险**:主体写出来发现 ~350 行,超预算。

**兜底**:
- 块 5(4 阶段流程一览)是主要预算消耗,如果超,把每阶段 bash 命令从 3 个砍到 1 个(主命令),其余迁 references/
- 块 4 + 块 10 关键不变量保留 30 + 15 = 45 行,不能砍

---

## 7. reviewer subagent prompt(全新 session 审 W1 收尾,主线程派时用)

```
你是 W1 reviewer subagent — 全新 session,read-only。审 W1「拆 SKILL.md 1480 → ≤ 300 + references/ 6 文件」的 diff + spec。

读 4 个文件:
1. refactor_specs/wave_01_split_skill_md.md(本 spec,看「应该是什么样」)
2. ~/.claude/skills/fengyun-publish/SKILL.md(新主体,看「实际怎么样」)
3. ~/.claude/skills/fengyun-publish/SKILL.md.pre-w1-bak(W1 前的原稿,做 diff 对照)
4. ~/.claude/skills/fengyun-publish/references/*.md(6 个新文件)

审核 4 维度:
1. 主体 ≤ 300 行?(`wc -l SKILL.md`)
2. references/ 6 文件齐?(`ls references/*.md`)
3. 跨章节 link 全活?(`grep -oE "references/[a-z_0-9]+\.md" SKILL.md` 验全)
4. 越界改内容?(diff `SKILL.md + references/*.md` 跟 `SKILL.md.pre-w1-bak` 字数 ± 5%)

binary verdict: ship / revise / major issue
不通过列具体行号 + 问题 + 建议。
报告 ≤ 1500 字,不许 emoji 不许时间预估。
```

---

## 8. Musk 监督员 prompt(全新 session 审 W1 过程合规)

```
你是 Musk 监督员 — 全新 session。读 elon-musk-perspective skill + REFACTOR_PLAN.md + refactor_specs/wave_01_split_skill_md.md。

跑 git log + diff 看 W1 实际执行轨迹。

5 维核验:
Q1 Idiot Index: 理想 1 commit vs 实际 N commit?
Q2 诚实程度: W1 commit message 跟实际改动对得上?
Q3 学习闭环: 有没有遵守 Musk 告诫「先派 subagent 再开工」(W1 explorer 应该是 git log 第一个动作之前就派的)
Q4 invariant #4「0 消费者 = 0 生产」: 主体新增内容有没有「将来要做」未实装假承诺?
Q5 subagent 真用 vs 假用: W1 §0 状态表 subagent 字段诚实?

binary verdict: 合规 / 偏离
```

---

## 9. W1 完工标准

全部满足才能 commit:

- [x] explorer subagent `a416e07e87ce1f343` 完工(✅ 已完工)
- [ ] 备份 SKILL.md.pre-w1-bak 存在
- [ ] references/ 6 文件齐全
- [ ] SKILL.md 主体 ≤ 300 行
- [ ] 跨章节 link 全活(grep 验证)
- [ ] verify subagent `verify_baseline.py` PASS
- [ ] reviewer subagent verdict: ship
- [ ] Musk 监督员 verdict: 合规
- [ ] REFACTOR_PLAN.md §0 W1 行更新 🚧 → ✅

---

## 10. 下一步执行清单(主线程严格按序)

1. ✅ 写 wave_01 spec(本文件,主线程刚完工)
2. ⬜ 备份 SKILL.md → SKILL.md.pre-w1-bak
3. ⬜ 创建 references/ 目录
4. ⬜ 6 个 references/ 文件逐个新建(从 SKILL.md 粘贴对应行号,不改字)
5. ⬜ 重写 SKILL.md 主体(≤ 300 行 12 块结构)
6. ⬜ 跨章节 link 改路径 + grep 验证
7. ⬜ 派 verify subagent 跑 baseline + W1 专有验收
8. ⬜ 派 reviewer subagent 全新 session 审 diff + spec
9. ⬜ 派 Musk 监督员全新 session 审过程合规
10. ⬜ 三者全过 → commit + 更新 REFACTOR_PLAN.md §0 W1 行 ✅
