# Stage 2 Write — 详细 SOP

> 主体跳转:`SKILL.md` Stage 2 / 4 · Write
> 跨阶段约束:见主体「关键不变量」段(R18 红线 / image_paths 非空 / north_star 必填 / writer 真 invoke)
> 本文件来源:SKILL.md.pre-w1-bak L348-553,W1 纯拆分不改字段
>
> **⚠️ W4(2026-05-27)**:`writer_pass`/`title_pass`/`ending_pass` + `*_real_run`/`*_source` 已迁 invocation log。
> 写完整稿 + title/ending harness 后写 `writer.invocation.json`
> (`python tools/invocation_log.py write --slug <slug> --stage writer --skill fengyun-writer --input-file <research> --output <draft> --result written`);
> frontmatter 只留 metadata。下文 frontmatter pass_flag 写法是 W4 前历史描述 —— 以本 banner + `frontmatter_checklist.md` 为准。

---

## Step 3 · 写初稿

调 **fengyun-writer** skill(默认):
- 触发语:`用 fengyun-writer 写一篇关于 <主题> 的草稿,北极星是「<填空>」,事实清单见 output/research/YYYYMMDD-<slug>.md`
- 让 fengyun-writer 自己跑它的 Step -1 / 0 / 1 / 2 / 3 流程
- 输出落到 `output/drafts/YYYYMMDD-<slug>-v0.md`,frontmatter 必带 `title / digest / author: 研究Agent的云`

**⛔ Round 22 P0-6 fake-pass 防伪铁律**:
- frontmatter `writer_pass: true` 时,**必须**同时写 `writer_real_run: true` + `writer_source: "fengyun-writer skill v1, round=1, 4200 字"`
- gate.py 看到 `writer_pass: true` 但缺这两个字段 → 当场阻断 ship
- 主线程绝对不许「拍脑袋自己扮 writer 写完直接标 pass」— 必须真 invoke fengyun-writer skill

##### → 立即写入 frontmatter(Step 3 完成后,不许攒到最后)

```yaml
writer_pass: true
writer_real_run: true
writer_source: "fengyun-writer skill v1, round=1, 4200 字"
```

3 个字段,一个都不能少。写完才进 Step 3.3。

> **W2.C3 注**:原「卡兹克风格 / System A 风格 例外切换」段已删除(2026-05-27)。
> invariant #2 统一语言:fengyun-publish 不支持双轨切换。用户要卡兹克风格直接 invoke
> khazix-writer skill,不走 fengyun-publish 流程。

## Step 3.3 · 标题 harness 循环(Round 16 新增,2026-05-25)

**用户原话(2026-05-25)**:「就做标题党 — PHASE1 数据有规律可以直接用 — title harness 是必要的」

**问题根因**:最近 ship 文章都是 AI 系统产出,「风云碰巧做对了」≠「风云本人判断力」。AI 系统当前没有标题硬约束,**6 篇 ship 真稿在 PHASE1 标题规律上只有 1/6 pass**(详见 `reports/title_hook_formulas.md` 78 篇双高数据)。下一次 AI 产出可能就翻车 — 必须 lock 数据规律。

**用户 Q1 拍板:A. lock PHASE1 数据规律,强制改成 20+ 字命中钩子**(2026-05-25)

##### Step 3.3 完整流程(harness 循环)

**DEFAULT:跑标题 harness(上限 3 轮,不达标用最后一版)**。`title` 初值 = draft frontmatter 的 title。每轮:

1. **L1 评分 + L2 去重**(真 CLI:title_signal 评分(给 hook_type)→ title_dedup 去重;`<TITLE>`/`<e1>`/`<N>` 由主线程从 draft 填):
   ```bash
   # L1 评分:输出含 hook_type,供下一步 --hook-type <H>
   python tools/title_signal.py --title "<TITLE>" --topic-keywords <e1> <e2> --body-chars <N>
   # L2 去重:--draft 排除自身(Bug 4)
   python tools/title_dedup.py --title "<TITLE>" --hook-type <H> --max-age-days 14 --max-n-check 10 --draft output/drafts/<slug>-v0.md
   ```
   - `pass` = signal `verdict==pass` + dedup `is_too_similar==false`(主线程合成两个 JSON)
   - `--topic-keywords` = Step 2 ITI 出的实体;`--body-chars` = 正文字数(主线程从 draft 算,或省略改用 `title_signal --draft <md>` 自动抽)
   - **Bug 4**(Round 17):Step 3.3 时 draft 已存在于 `output/drafts/`,**必须**传 `--draft`(→ current_draft_path)排除自身,否则 self-match Jaccard=1.0 必然撞型
2. `pass`(signal `verdict==pass` + dedup 不撞型)→ break
3. 否则 invoke `fengyun-writer` skill(改标题模式,**只改 frontmatter title,不改正文**),feedback = `signal.redo_feedback | dedup.redo_feedback`;新标题写回 frontmatter,回 1
4. 到第 3 轮仍不过 → 用最后一版(用户原话锁定)

##### 评分维度(全部 PHASE1 实证,反 p-hacking 合规)

| 维度 | 阈值 | 出处 |
|---|---|---|
| 字数 ∈ [20, 40] | < 20 字小样本陷阱 | PHASE1_FACTS line 810 |
| 数字组数 ≤ 1 | 双高 0.36 vs 假爆款 0.70 | line 302 / 423 |
| 品牌词白名单(主题相关时必上)| Anthropic / Claude / Skills / Claude Code | line 691-698 |
| 品牌词黑名单不上 | OpenAI / GPT / Veo / GLM 已脱热 | line 698(-9.3pp)|
| 命中 7 钩子之一(**W9 软分**)| 颠覆认知 / 实用指南 / 热点事件 / 人物故事 / 思维比喻 / 深度拆解 / 未来预言 | `reports/title_hook_formulas.md`;W9 从 hard gate 改软分(B4 卡掉 72% 卡兹克爆款)|
| 4 共同特质 ≥ 1/4(**W9: ≥2→≥1**)| 反常规认知 / 强行动指令 / 高信息密度 / 情绪化表达 | B4 ≥2 仅 3.4% |
| ~~致命组合~~(**W9 已砍**)| B4 0/321 命中(tb_ratio 用 body_chars=5000 永不触发);tb_ratio/english_chars 留 advisory | — |
| token Jaccard ≤ 0.40 | 跟近 14 天 ship 标题 | 镜像 opening_dedup |
| 5-gram 重叠 ≤ 0.25 | 同上 | 同上 |
| 钩子类型 7 天内 ≤ 1 次 | 防钩子连续撞 | 自加 |

##### 关键设计原则(跟 opening/ending harness 一致)

- **上限 3 次**:不达标就用最后一版(用户原话 2026-05-24)
- **只改标题不改正文**:writer 接 frontmatter title 改的 prompt,不重写 4000 字正文
- **跑在 Step 3 之后 / Step 3.5 ending 之前**:因为标题决定后,封面 routing(Step 7)依赖标题 + 前 500 字
- **失败回退**:`title_signal` / `title_dedup` 跑挂 → 跳过 Step 3.3,记 `degraded.title_harness = "module fail"`,不阻断 ship

##### → 立即写入 frontmatter(Step 3.3 完成后)

```yaml
title_pass: true
title_real_run: true
title_source: "title_signal hook_type=X, score_title N/10, dedup Jaccard=0.XX"
```

写完才进 Step 3.5。

## Step 3.5 · 结尾 harness 循环(Round 14 新增,2026-05-24)

**问题根因**:最近几篇结尾同质化(「不是 X 是 Y / 引古典 / 愿你也能 + 颜文字」公式重复)。

**数据驱动锁定**(跟开头不同,**结尾有 4 个 PHASE1 真信号**):
- `b_last_para_chars` 跨 4 账号 ρ=+0.300 4/4 显著
- `viral_design_composite` ρ=+0.226 4/4 显著
- `viral_sharing_addr` ρ=+0.215 4/4 显著
- `viral_ending_strength` ρ=+0.201 3/4 显著
- TOP 5% 爆款 vs 扑街 8 个 STRONG 差异维度(末段字数 +143% / aphorism +213% / imperative +49% / summary +108%)

**解法**:跟开头镜像设计 — **3 关 + 上限 3 次 harness 循环**:

**DEFAULT:跑结尾 harness(L1 改末段 → L2 评,上限 3 次,不达标用最后一次)**。每轮:

1. **L1 写/改末段**:
   - 第 1 次:Step 3 已写完整稿,直接评
   - 第 2/3 次:invoke `fengyun-writer` skill(改末段模式,**只改最后 ## 章节,不重写全文**),基于上轮 `redo_feedback`
2. **L2 评**(3 关;真 CLI:ending_signal 评分 + ending_dedup 去重,读 draft 全文):
   ```bash
   python tools/ending_signal.py --draft output/drafts/<slug>-v0.md
   python tools/ending_dedup.py --draft output/drafts/<slug>-v0.md --max-age-days 30 --max-n-check 5
   ```
   - `all_pass` = signal `verdict==pass` + `physical_pass` + dedup `is_too_similar==false`(主线程合成两个 JSON)
   - **Bug 4**(Round 17):draft 已存在,ending_dedup 的 `--draft` 同时作 current_draft_path 排除自身
3. `all_pass`(signal `verdict==pass` + `physical_pass` + dedup 不撞型)→ break
4. 否则记 `redo_feedback`(signal + dedup 各自的)→ 回 1 重试
5. 到第 3 次仍不过 → 用最后一次结尾继续(用户原话锁定);history 写 run log

**3 关详解**(数据驱动,跟开头方法论同源):

| 关 | 内容 | 阈值来源 |
|---|---|---|
| **L2-a 物理约束** | 末段(最后 H2 之后所有段)≥ 150 字 | PHASE1 `b_last_para_chars` 跨 4 账号 ρ=+0.300 4/4 显著(对风云 voice 友好的保守阈值) |
| **L2-b 4 维信号** | 金句密度 / 摘要密度 / 召唤密度,每维 ≥ 6/10 | viral_design_features 跨 4 账号验证,TOP 爆款 vs 扑街 STRONG 差异维度 |
| **L2-c 近期结尾去重** | token Jaccard ≤ 0.30 + 5-gram ≤ 0.20 | Jobs syntactic(跟 opening_dedup 镜像) |

**写在 Step 4 lint 之前**:
- Step 3 完整稿写完 → Step 3.5 ending harness(改的是末段不是全文)→ Step 4 lint
- 改末段不破坏物理约束(只动「## 收束」/「## 收尾」段内容,不动其它章节)

##### 关键设计原则(跟 opening harness 一致)

1. **改末段不改全文**:retry 时让 writer 只改最后一个 H2 之后的内容,**不动主体论证**
2. **上限 3 次**(用户锁定,跟 opening 一致)
3. **3 次不过用最后一次**(避免阻塞主流程,Real Artists Ship)
4. **history 写 run log**(数据飞轮回填将来校准阈值)

##### → 立即写入 frontmatter(Step 3.5 完成后)

```yaml
ending_pass: true
ending_real_run: true
ending_source: "ending_signal score_ending N/10, dedup Jaccard=0.XX"
```

写完才进 Step 4(详见 `references/stage_03_verify.md`)。
