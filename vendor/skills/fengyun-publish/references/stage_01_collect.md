# Stage 1 Collect — 详细 SOP

> 主体跳转:`SKILL.md` Stage 1 / 4 · Collect
> 跨阶段约束:见主体「关键不变量」段(R18 红线 / image_paths 非空 / north_star 必填)
> 本文件来源:SKILL.md.pre-w1-bak L58-346,W1 纯拆分不改字段

---

## Step 1 · 确认主题 + 北极星填空 + 数据驱动选题(Round 11,2026-05-24)⛔ BLOCKING

**新增数据驱动子步骤**:不再凭主观挑「热点」,用 System A PHASE1 + topic_hotness.parquet 给候选打分。

### Step 1.0(新)ITI 架构数据驱动候选排序

**Round 12 升级 2026-05-24**:从 aihot 单源升级到 **ITI 第一段聚合**(用户自创 ITI 架构,见 user-level memory `feedback_iti_architecture.md`)。

**信源覆盖说明**:用 5 个「聚合源」间接覆盖 40+ 底层源(aihot/TrendRadar/smol.ai 自己已经合并了多个底层 RSS),**避免重复调 67 个 RSS**。**W8 E2**:TrendRadar 升级为直接读 `output/rss/<date>.db` **按 feed 维度取最新 N=5 条**(`--per-feed-n` 可调),拿全量 per-feed 覆盖而非只读 `latest_daily.md` 摘要;DB 空/过期/异常 → 自动回退旧 markdown reader,再过期才 WebSearch 补位。

**DEFAULT:必跑 ITI 数据驱动选题**(I-1 广搜 → T 排序 → T 去重)。
**Opt-out**:仅当用户消息**显式**含「主题已定」/「跳过选题」/「用 X 主题」时,跳过本步直接用指定主题。

**1a. I-1 Python 信源**(iti_collect 真 CLI,5 个源):
```bash
python tools/iti_collect.py --hours 24 --out output/runs/<slug>/iti_pool.json
```
- `items` = 15-30 条候选(硬约束 ≥10 两位数);上限 30
- exit code 3 = degraded(候选 < 10,降级继续);exit 0 = 正常

**1b. I-1 WebSearch 补位**(主线程必跑,用户原话「两个 I 都要用上 WebSearch」):逐个调 WebSearch 工具,4-6 个 generic query 覆盖 Python 脚本拉不到的源:
- `今日 AI 大事件` / `AI today industry news` / `Anthropic OpenAI 最新动态` / `Claude Skills latest`
- TrendRadar 旧时(`degraded.trendradar=true`)额外加:`AI newsletter Stratechery Semianalysis 本周`
- 把 WebSearch 结果归一化后写 `output/runs/<slug>/ws_items.json`(供下一步合并)

**1c. 合并 + T 排序 + T 去重**(真 CLI:topic_recommender 排序 → event_dedup 去重;合并 Python 池 + WebSearch 池):
```bash
# T 排序:pool.items + WebSearch 池 → ranked.json(每项加 _predicted_burst_rate / _matched_family / ...)
python tools/topic_recommender.py --pool output/runs/<slug>/iti_pool.json --ws output/runs/<slug>/ws_items.json --out output/runs/<slug>/ranked.json
# T 去重:逐条 event_dedup,输出首个非撞型 chosen + filtered 列表 → chosen.json
python tools/event_dedup.py --in output/runs/<slug>/ranked.json --days 7 --include-published --out output/runs/<slug>/chosen.json
```
- `topic_recommender.py` 每项加 `_predicted_burst_rate`(0-1)/ `_matched_family` / `_matched_keywords` / `_reason`(PHASE1 + topic_hotness.parquet 排序)
- **Bug 4**(Round 17):Step 1.x 时还没写 draft,`event_dedup` 无自身可排除 → 不传 `--current-draft`;但 Step 6.5 / 7 之后复跑 dedup **必须**传 `--current-draft output/drafts/<slug>-v0.md`
- 全自动选 `chosen.json` 的 `chosen`(= filtered top 1,burst_rate 最高);content-judge D-5 选题胆量自动二筛,不过则顺位取 `filtered` 里下一个候选(无人工挑选);top 10 留痕 run log

**降级路径**(I-1 失败时):
- 6 信源全失败 → fallback 到原 aihot 单源调用(保留旧路径兼容)
- pool_result["degraded"] = True(候选 < 10)→ 报警但继续,标记 run log `degraded.iti_collect = True`

**数据驱动锁定**(PHASE1 v2 验证):
- ✅ **优先**:Anthropic Skills(92%)/ Claude Code(87.5%)/ Vibe Coding(85.7%)/ Karpathy(88.9%)
- 🟡 **次优**:Anthropic/Claude 家族(67.8%)
- ❌ **避免标题凸显**:OpenAI / GPT(-9.3pp)/ 智谱 / GLM(-23.2pp)/ Sora / Veo(-47.2pp)
- ⚠️ **过气**:提示词工程(2026-02→04 hotness 0.84→0)/ DeepSeek / Cursor

### Step 1.1 抽核心事件

1. 从用户输入抽出核心事件。只给主题词(如「Anthropic 新规」)时,**自动抽取最具体的核心事件**继续(全自动,不向用户确认)
   - **DEFAULT**:用 Step 1.0 数据驱动选题 top 1;**Opt-out**:用户显式给定主题则用其指定事件
2. **必须填**北极星空白:**「读者读完应该感受到 ___」**(一句话,< 30 字,是感受不是知识)
   - 写不出来 → 不开始(fengyun-writer Step -1 已要求)
   - 不许把这一步「内化」掉,要打出来给用户看,并写进 `output/research/YYYYMMDD-<slug>.md` 顶端
3. 生成 `slug`:核心事件的英文/拼音短标签(如 `anthropic-rsp-v2` / `claude47-skills`),用于文件命名

### Step 1.2(新)事件去重 check

`event_dedup.check_event_dedup({title, summary}, days=7)` 必跑。如果 is_duplicate=True:
- 记 run log「最近 7 天已 ship 过同事件 <matched_title>」
- **全自动顺位**:自动跳过该事件,取 Step 1.0 排序里的下一个候选(无人工 confirm)
- 若 top 10 全部撞型(罕见)→ 记 degraded,用 top 1 继续(数据飞轮回填看是否要扩候选池)

### Step 1.3(关键铁律 2026-05-24)

**❌ 不要做的事**(我之前犯过):
- 「连续 3 篇 Anthropic = 主题集中度告警」 — **反 PHASE1 数据**(Anthropic 系连写都在涨)
- 「类别要轮换 industry → paper → tip」 — **没数据支持**
- 「主观判断读者疲劳」 — 没数据,subjective

**✅ 真正该做的**:
- 数据驱动 burst_rate 排序(PHASE1 + topic_hotness)
- 同一事件 7 天去重(不是同主题)
- 风云 lived stake 二筛(从高 burst_rate 池里挑作者能写的)

## Step 1.5 · dogfood gate(Round 7 P0,2026-05-24)⛔ BLOCKING

**目的**:Jobs Apple 内部 dogfood 原则在 IP 写作的对等机制 — 风云在大规模写作之前先确认「这个开头是不是我」。避免后续 3 轮改稿改的是 voice drift,不是真正的内容问题。

**触发条件**:Step 1 北极星填空完成,Step 2 调研开始之前。

### 流程

#### Round 13 升级(2026-05-24):开头 harness 循环

**问题根因**:最近几篇开头同质化(「前几天看到 → 念了几遍 → 第一反应」公式重复)。

**解法**:试稿后增加 **3 关 / 上限 3 次 retry** 的 harness 循环 — Musk × Jobs 第一性原理(数据驱动 + 反过拟合)。

**DEFAULT:跑开头 harness 循环(L1 写 → L2 评 → retry,上限 3 次,不达标用最后一次)**。每轮:

1. **L1 写**:invoke `fengyun-writer` skill 试稿模式(出 200 字开头,不出完整稿)
   - 第 1 次:正常试稿
   - 第 2/3 次:prompt 注入上轮 `redo_feedback`,让它避开上次问题
   - 把本轮试稿写到 `output/runs/<slug>/opening_trial.txt`
2. **L2 评**(3 关;真 CLI:opening_signal 评分 + opening_dedup 去重,主线程读两个 JSON 合成 all_pass):
   ```bash
   python tools/opening_signal.py --trial output/runs/<slug>/opening_trial.txt
   python tools/opening_dedup.py --trial output/runs/<slug>/opening_trial.txt --max-age-days 30 --max-n-check 5
   ```
   - `all_pass` = signal `verdict==pass` + `physical_pass` + dedup `is_too_similar==false`(主线程合成两个 JSON 输出)
   - **Bug 4**(Round 17):Step 1.5 时 trial 是临时文件,尚未写到 `output/drafts/`,无自身可排除 → 不传 `--current-draft`;但 Step 6.5 revise loop 复跑 opening dedup **必须**传 `--current-draft output/drafts/<slug>-v0.md` 防 self-match
3. `all_pass`(signal `verdict==pass` + `physical_pass` + dedup 不撞型)→ 接受该试稿,break
4. 否则记 `redo_feedback`(signal + dedup 各自的 feedback)→ 回 1 重试
5. 到第 3 次仍不过 → **用最后一次试稿继续**(不 abort,用户原话锁定);全程 history 写 run log

**3 关详解**(Musk × Jobs 共识):

| 关 | 内容 | 阈值 | 来源 |
|---|---|---|---|
| **L2-a 物理约束** | 真首段(W9: 真·首段,非整 intro 块)≥ 25 字(W9: 50→25,B4 median 26)+ 第一人称密度 ≥ 5/千字 | PHASE1 跨账号真规律 + TOP 5% 爆款 +12.5pp 实测 | `opening_signal.check_physical_constraints` |
| **L2-b 公式新鲜度**(**W9 砍 具体性/反差感/情绪锚点动词维/信息密度** — B4 命中率 87.2%/6.6%/—/100% 零判别力)| 公式新鲜度 ≥ 6/10(唯一保留评分维)| B4 实测 + Musk 第一性原理 | `opening_signal._score_formula_freshness` |
| **L2-c 近期开头去重** | 跟最近 5 篇 ship 过开头 token Jaccard ≤ 0.30 **且** 5-gram 重叠 ≤ 0.20 | Jobs syntactic 反复读检测(用户 2026-05-24 强调) | `opening_dedup.check_opening_overlap` |

**关键设计原则**:
1. 任一关不过 → redo(把 redo_feedback 反馈给 writer 让它知道改啥)
2. 上限 3 次(用户原话「上限三次,还没达到标准就直接用最后一次的就行」)
3. 3 次都没全过 → 不 abort,**用最后一次继续**(避免阻塞主流程)
4. 全程 history 写 run log,数据飞轮回填(将来 train signal 阈值)

#### Step 1.5 完整流程(harness 循环 + dogfood gate)

1. invoke `fengyun-writer` skill **试稿模式**(只出 200 字开头,不出完整稿):

```
用 fengyun-writer 试稿:基于「<北极星填空>」+「<核心事件>」,
出 200 字开头(不出完整稿)。
风格遵循 voice-dna.md + corpus/growth/ 抽 3-5 篇感受语调。

【Round 13 新增 — opening loop avoidance】
如果是 retry(attempt > 0),writer 必须避免上次的 redo_feedback:
  上次反馈: <opening_loop_history[-1]["feedback"]>
  本次必须解决: 上面提到的具体维度
```

2. **开头 harness 循环**(L2 评估 + L3 retry,见上节伪代码)— 上限 3 次

3. **调 content-judge skill D-1 代答(Round 9 NORTH_STAR 红线)**:

```
用 content-judge skill D-1 dogfood gate 判断:
输入 = 200 字试稿全文
输出 = {verdict: y|n, confidence: 0-1, reason: "...", degraded: bool, voice_5dim: {...}}

D-1 跑 voice-dna 5 分量(语调/共情/Vision/典故/底色) + R18 硬否决预检
置信度公式:
  5/5 过 → 0.9 y
  4/5 过 → 0.75 y
  3/5 过 → 0.55 → fallback
  R18 命中 → 1.0 n
```

3. 行为按 D-1 输出走(全自动,无人工):
   - `verdict=y` 且 `confidence ≥ 0.7` → **自动进 Step 2 调研**(M4 红线)
   - `verdict=n` 且 `confidence ≥ 0.7` → **自动重跑 fengyun-writer 试稿**(不消耗 Step 6.5 改稿额度);最多重跑 2 次,2 次还 n → **自动顺位换 Step 1.0 排序里的下一个主题候选**(记 run log,不halt 不打扰)
   - `degraded=true` (confidence < 0.7) → 5 分量矩阵 + 试稿 + 历史快照写 run log,**自动 degraded continue**
   - R18 命中 → 不重跑,**自动顺位换下一个主题候选** + 标记 `R18 pre-trigger`(无人工修主题)

4. 把 dogfood verdict 记到 `output/runs/YYYYMMDD-<slug>.json` 的 `dogfood_gate` 字段:
   `{first_pass: y/n, retries: 0-2, final: y/n, confidence: <float>, source: "content-judge D-1" | "human fallback", complaints: ["..."]}`

> **W2.C4 注**:原步骤 4「数据飞轮 v1 自动 log 写 founder_feedback.jsonl」已删除(2026-05-27),
> 0 消费者 = 0 生产 invariant 落地。真需要数据飞轮时重新设计。

### 为什么必跑

Round 7 Musk × Jobs 共识:**风云不读自己的草稿就推出去 = 反 dogfood**。fengyun-writer 蒸馏自 57 篇语料,但**没有「风云本人确认蒸馏对不对」的 ritual**,把关就成了走过场。Step 1.5 把这个 ritual 强制化,让 voice drift 在 200 字开头就被截住,**不等 4000 字写完再发现**。

### 跟 Step 6.5 改稿循环的关系

Step 1.5 dogfood gate **不消耗** Step 6.5 的改稿配额(还没出完整稿,只是开头试稿)。Step 6.5 改稿循环留给真正的 critic 反馈(双轨 B+C vote 出来后;改稿轮次天花板在 critic_vote.py 代码层裁决)。详见 `references/stage_03_verify.md#step-65-critic-revise-loop`。

### 失败回退

- fengyun-writer skill 不存在 / 试稿失败 → 跳过 Step 1.5,记 `degraded.dogfood = "writer skill missing / writer fail"`,继续 Step 2,但 run log 标记此次 ship 没过 dogfood
- **content-judge skill 不存在** → 回退到旧版「自动 degraded continue(不打扰用户)」流程,记 `degraded.dogfood_decision = "content-judge skill missing, auto-continue"`

## Step 2 · ITI I-2 深搜调研(Round 12 升级 2026-05-24)

**ITI 架构第三段 Information(深搜)**:基于已选定的 slug + entities,反向激活相关搜索源。

**重要(W8 E1 升级)**:**I-2 不再镜像 I-1 的 4 个 generic WebSearch query**。深搜改为「WebFetch T 选定主源 URL + aihot `?q=` 实体搜索 + 1 个 topic-specific 补充 query」,只补 Python 脚本拉不到的角度,不重跑 I-1 已经跑过的广搜。

不许凭空写,**事实 = 出处**(MEMORY 中的 `feedback_no_speculation.md` P0 铁律)。**ITI I-2 调用模式**:

1. **I-2 深搜三路(W8 E1,不再镜像 I-1 的 4 个 generic query)**:
   - **WebFetch 主源**:取 T 选定候选的主源 url(`chosen.json` 的 `chosen.url`)→ 作 `--main-source-urls`
   - **aihot `?q=`**:`explore_topic` 已内置 `aihot-query` 源(实体定向关键词搜索,7 天窗,复用 `iti_collect.fetch_aihot_by_query`),无需主线程手调
   - **1 个补充 WebSearch**(topic-specific,只补 Python 脚本拉不到的角度,不重跑 I-1 的 generic 广搜):如 `<title> 最新 分析`
   - 把归一化后的 ws_items 写 `output/runs/<slug>/ws_items_i2.json`(取其 top url 作 `--main-source-urls`)
2. **explore_topic + merge → facts.json**(真 CLI:`--merge-ws` 把 explore_topic 本地 facts 跟 WebSearch 池一步合并落 facts.json;`--main-source-urls` 取 ws_items_i2 的 top 4 url):
   ```bash
   python tools/iti_explore.py <slug> "<title>" --entities Anthropic OpenAI 融资 估值 --main-source-urls <ws_top1_url> <ws_top2_url> <ws_top3_url> <ws_top4_url> --merge-ws output/runs/<slug>/ws_items_i2.json --out output/runs/<slug>/facts.json
   ```
   - explore_topic 独立真 CLI(不需要 merge 时):`python tools/iti_explore.py <slug> "<title>" --entities Anthropic OpenAI 融资 估值 --main-source-urls https://a https://b`
   - `res['facts']` = 5 个本地 + API 源:we-mp-rss 同主题历史 / corpus grep 4 对标号同主题 / arxiv 主题搜索 / topic_hotness 历史数据点 / safe_webfetch 反爬主源
   - 合并 WebSearch + local facts → 目标 15-25 条,落 `facts.json`(再整理进 research.md)

并发派下面这些工具,聚合到 `output/research/YYYYMMDD-<slug>.md`:

- **WebSearch**:1 个 topic-specific 补充 query(W8 E1,不重跑 I-1 的 generic 广搜)
- **WebFetch**:T 选定主源 + 核心事件源(官方 blog / paper / GitHub release)2-3 个 URL
- **aihot `?q=`**:已内置 `explore_topic` 的 `aihot-query` 源(实体关键词搜索,查重 + 角度参考)
- **(可选)hv-analysis skill**:如果是产品/公司/概念主题,跑横纵分析法
- **(可选)corpus 检索**:在 `D:\Dev\ai-wechat-pipeline\corpus\` 里 grep 主题,看 4 个对标号写过没

输出 `output/research/YYYYMMDD-<slug>.md` 包含:
- 北极星填空(从 Step 1)
- 核心事件 3 句话摘要
- 5-10 条带 URL 的事实清单
- 3-5 条「我的角度可以是 ___」候选
