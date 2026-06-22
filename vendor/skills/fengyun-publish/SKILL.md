---
name: fengyun-publish
description: 风云 AI 公众号 end-to-end ship orchestrator。一句话触发就把 4 阶段 Collect → Write → Verify → Publish 跑完。当用户说「ship 一篇关于 X」「今天发一篇」「走完整流程」「全自动写一篇」或只给一个主题加「自动」时使用。只在「研究 Agent 的云」公众号项目语境激活,工作目录默认 `D:\Dev\ai-wechat-pipeline\`。最终人工动作只有一个:风云在公众号草稿箱手动发出。
---

# fengyun-publish — 风云 AI 公众号 ship orchestrator

编排层 skill,把已有的写作 / lint / critic / 视觉 / 发布资产串起来。

## Overview / When to use

任意一种说法即激活:

- 「ship 一篇关于 X 的文章」/「ship X」
- 「今天发一篇」/「今天发关于 X」
- 「走完整流程 / 跑完整流程」
- 「全自动写一篇」/「自动 ship 一篇」
- 用户只给主题/话题/事件 + 任意"自动 / 自己跑 / 一句话搞定 / 别问我"字眼

不激活的反例(走 fengyun-writer 而不是本 skill):

- 「用我的风格写一段 X」(只写不发,fengyun-writer)
- 「帮我看下这段」(只评,critic)
- 「改一下这篇 draft」(改稿,fengyun-writer)

---

## ⛔ 关键不变量(首部一份,首尾各一份防 Lost in Middle)

**北极星 — 每一步都问两个问题**(`NORTH_STAR.md`):
1. 这件事让「点击率」涨多少?(模块 1 钩子)
2. 这件事让「完读率/转发率」涨多少?(模块 2 深度)

两个都「不清楚」或「微小」→ 该步降级或跳过。

**三铁律(任一违反 = ship 阻断)**:
- ⛔ **R18 红线**:R18-P0(明确自指 AI 身份)= 机密红线,force_ship 兜底不适用。**全自动处理**:未到天花板 → revise 自动删段修;改到天花板仍 P0 → aborted_r18 自动终止(ERROR 日志,不 ship 自爆稿,无人工)。R18-P1/P2 不阻断 ship 但 writer 必须改
- ⛔ **image_paths 非空**:Round 25 物理硬约束 — 每篇 ship 必须有 ≥ 1 张图,文件物理存在 + size ≥ 5 KB(placeholder `assets/placeholder-sketch.png` 合法)
- ⛔ **north_star 必填**:Step 1.1 必填空白「读者读完应该感受到 ___」(< 30 字,是感受不是知识),不填不许进 Step 2

**真调防伪(W4)**:每个 stage 跑完写 `output/runs/<slug>/<stage>.invocation.json`(取代旧 frontmatter `*_pass`/`*_real_run`/`*_source`);gate 查 6 件 pre-publish 齐全 + `input_hash` 匹配当前稿 + `verify.result`∈{ship,force_ship}。详见 `references/frontmatter_checklist.md`。

---

## 4 阶段流程

### Stage 1 / 4 · Collect(选题 + 调研)

ITI 三段漏斗(I-1 广搜 → T 选题 → I-2 深搜)+ 北极星填空 + dogfood gate。

**必跑命令骨架**:
- `python tools/iti_collect.py --hours 24 --out output/runs/<slug>/iti_pool.json`
- `python tools/topic_recommender.py --pool output/runs/<slug>/iti_pool.json --ws output/runs/<slug>/ws_items.json --out output/runs/<slug>/ranked.json` 排序 → `python tools/event_dedup.py --in output/runs/<slug>/ranked.json --days 7 --include-published --out output/runs/<slug>/chosen.json` 去重(exact 命令见 stage_01)
- I-1 主线程 WebSearch 4-6 个 generic query 补位;I-2 不镜像 I-1(W8 E1)= WebFetch T 选定主源 + aihot `?q=`(已内置 explore_topic)+ 1 个补充 query
- `python tools/iti_explore.py <slug> "<title>" --entities ... --main-source-urls ... --merge-ws output/runs/<slug>/ws_items_i2.json --out output/runs/<slug>/facts.json`
- 调 fengyun-writer 试稿 200 字 → 跑 opening_signal harness(3 关 + 上限 3 次)→ content-judge D-1 dogfood gate

**输出**:`output/research/YYYYMMDD-<slug>.md`(含北极星 + 5-10 条带 URL 事实 + 3-5 条角度候选)

**详见**:`references/stage_01_collect.md`

---

### Stage 2 / 4 · Write(写初稿 + 标题信号检查)

调 fengyun-writer skill 写 4000-5000 字 → 跑一次 title_signal + title_dedup 出参考信号(**ADVISORY 不拦路**;v2.0 2026-06-10 降档,依据 W9 审计见 stage_02)。**ending harness 已删**(v2.0:W9 审计证伪判别力,结尾质量由王小波 + 花叔 Track B 把守)。

**必跑命令骨架**:
- 调 `fengyun-writer` skill(完整稿模式,不许主线程手写)
- 标题打分 `python tools/title_signal.py --title "<TITLE>" --topic-keywords <e1> <e2> --body-chars <N>` + `python tools/title_dedup.py --title "<TITLE>" --hook-type <H> --draft output/drafts/<slug>-v0.md`(跑一次记 run log;fail 给 writer 一次自主改标题机会,不循环不回评;exact 见 stage_02)

**关键设计**:
- 标题检查 advisory:fail 不阻断 ship;dedup 撞型信号参考价值最高,writer 应优先采纳
- title_dedup 必须传 `current_draft_path=draft_path` 防 self-match
- 改稿只动局部不重写全文

**详见**:`references/stage_02_write.md`

---

### Stage 3 / 4 · Verify(机械 lint + 语感 + critic 投票)

四道关卡串行,失败回到 Step 6.5 改稿循环。

**必跑命令骨架**:
- `python tools/fengyun_lint.py <draft>` — 必跑直到 0 violation(R0-R18 + R19-R28 huashu 规则 + R29 破折号 ≤ 3/篇 + R30 否定式排比 ≤ 2/篇)
- 调 `wangxiaobo-perspective` skill — 翻译腔预审
- 双轨 critic 并行(single message 多 Skill tool call,W2.C6 删 Track A score_draft):
  - Track B:调 `huashu-perspective` skill — binary ship/不 ship(prompt 保持严格,不提轮次)
  - Track C:调 `content-judge` skill — binary 挂名意愿(prompt 保持严格,不提轮次)
- `python tools/critic_vote.py --all-rounds <rounds.json>` — 双轨 gate_tree + 隐藏天花板决议

**决议路径**(全流程无人工交互):`ship` 进 Stage 4 / `revise` 进 Step 6.5 改稿循环(R18-P0 也走这里自动删段)/ `force_ship`(隐藏 3 轮天花板强制 ship + WARN)进 Stage 4 / `aborted_r18`(改到天花板仍自爆 AI → 自动终止 + ERROR 日志,不 ship,无人工)。⛔ 双轨对等(任一拒绝即 revise),评委 prompt 永不出现「轮次/上限」。

**详见**:`references/stage_03_verify.md`

---

### Stage 4 / 4 · Publish(封面 + 内文图 + 推草稿)

**必跑命令骨架**:
- 封面(无模板,W7):抽 title/subtitle(≤14/≤22)→ 调 `huashu-image-curator` skill **Mode 3 cover** 自著中文 prompt → `python tools/seedream_client.py --prompt "<中文 prompt>" --aspect <16:9|2.35:1> --out output/images/<slug>-cover.png --style-anchor "<anchor>"`(retry ×3 + placeholder fallback 内藏;exact 命令见 stage_04)
- `python tools/illustrate_decider.py output/drafts/<slug>-v0.md --dry-run` — Step 7.1 函数预筛候选位置(positional path + `--dry-run`)
- 调 `huashu-image-curator` skill Mode 2 — 花叔决策 0-5 张图位置 + prompt
- Step 7.3 内文图出图 `python tools/illustrate_decider.py --draft output/drafts/<slug>-v0.md --generate --decision output/runs/<slug>/image_decision.json --slug <slug>`(exact 命令见 stage_04)
- `python tools/post_fengyun_publish.py <draft>` — 渲染 huashu layout + 上传草稿

**输出**:`media_id`(草稿 ID)写到 `output/runs/YYYYMMDD-<slug>.json`

**Step 9 报告**:必须 print 全流程结果给用户(主题 / slug / 北极星 / 草稿 ID / critic 双轨 / force_ship 标记 / R18 触发 / lint / 改稿轮数 / 下一步)

**详见**:`references/stage_04_publish.md`

---

## 关键路径

- 项目根:`D:\Dev\ai-wechat-pipeline\`
- 草稿:`output/drafts/YYYYMMDD-<slug>-v0.md`(每轮改稿 v1 / v2)
- 封面:`output/images/YYYYMMDD-<slug>-cover.png`
- 内文图:`output/images/YYYYMMDD-<slug>-NN-*.png`
- 调研材料:`output/research/YYYYMMDD-<slug>.md`
- 跑批日志:`output/runs/YYYYMMDD-<slug>.json`
- 工具:`tools/{fengyun_lint,fix_punctuation,ship,post_fengyun_publish,critic_vote}.py`(W2.C6 删 score_draft;sop_v2_1 仍被 fengyun_anchor / verify_audit 使用,保留)
- 微信凭证:`.env`(`WECHAT_APPID` / `WECHAT_SECRET`)

---

## 失败行为概览

| 故障类 | 默认行为 |
|---|---|
| skill 不存在(huashu/wangxiaobo/content-judge)| 跳过该步,记 `degraded.<name> = "skill_missing"`,继续 |
| 双轨 critic 任一缺失 | 听另一轨 verdict + 标 degraded;双缺则 revise(详见 stage_03_verify.md 降级表)|
| 改稿到隐藏 3 轮天花板还没双过 | critic_vote.py 自动 `force_ship`(强制 ship + WARN 标记,全自动闭环)|
| R18-P0 命中(明确自指 AI 身份)| revise 自动删段修;改到天花板仍 P0 → `aborted_r18` 自动终止(ERROR 日志,不 ship,无人工)|
| 推送失败(网络/token/quota)| 留本地 HTML preview + 错误日志,不重试 |

**详见**:`references/failure_modes.md`(完整 13 项降级表 + System A vs B 切换 + 配套脚本 + 调试 hook)

---

## Output Format(Step 9 报告)

```
=== fengyun-publish ship 报告 ===
主题: <title>
slug: <slug>
北极星: <填空>

草稿 ID: <draft_media_id>
选用版本: <v0 / v1 / v2 / v3>

critic 双轨(末轮):
  B · huashu:     <ship/reject/skip>
  C · content-judge: <挂名/不挂名/skip>
  决议: <ship / force_ship / aborted_r18>

force_ship: <true/false>(true = 隐藏天花板强制 ship,WARN)
R18 触发: P0=<n> P1=<n> P2=<n>
机械 lint: 0 violations
改稿轮数: <n>

下一步: 公众号后台 → 草稿箱 → 人工最终审阅 + 发出
```

并把 JSON 版本写到 `output/runs/YYYYMMDD-<slug>.json` 留档。

---

## References

| 文件 | 详细内容 |
|---|---|
| `references/stage_01_collect.md` | Step 1.0 ITI 广搜 / 1.1-1.3 北极星 + 选题 / 1.5 dogfood + opening harness / 2 ITI I-2 深搜 |
| `references/stage_02_write.md` | Step 3 fengyun-writer / 3.3 标题信号检查(advisory)/ 3.5 已删(v2.0) |
| `references/stage_03_verify.md` | Step 4 lint / 5 王小波 / 6 双轨 critic vote / 6.5 改稿循环 + 隐藏天花板 |
| `references/stage_04_publish.md` | Step 7 封面 + 7.1-7.3 内文图 / 8 排版+推草稿 / 9 报告 |
| `references/failure_modes.md` | 降级总表 + System A/B 切换 + 配套脚本 + 调试 hook |
| `references/frontmatter_checklist.md` | frontmatter metadata + **invocation log**(W4 真调防伪,取代 frontmatter pass_flag)+ Round 25 image_paths 物理硬约束 |

---

## ⛔ 关键不变量(尾部一份,首尾各一份防 Lost in Middle)

重复首部 3 铁律 + 北极星 — 跑到 Step 9 时再看一遍:

1. **R18 红线**:P0 命中 → revise 自动删段;改到天花板仍 P0 → aborted_r18 自动终止(ERROR 日志,不 ship,无人工)。force_ship 兜底不适用(机密红线优先)
2. **image_paths 非空**:每篇 ship 必须 ≥ 1 张图(placeholder 合法)
3. **north_star 必填**:Step 1.1 不填不许进 Step 2

**北极星**:点击率(钩子)+ 完读率/转发率(深度)。两个都不清楚 → 降级或跳过。

**真调防伪(W4)**:每 stage 写 invocation log(`output/runs/<slug>/*.invocation.json`),gate 查 6 件齐全 + `input_hash` 匹配当前稿 + verify.result∈{ship,force_ship}。

## 风云手动只做的一件事

公众号后台 → 草稿箱 → 看草稿 → 觉得 OK → 发出。其余全自动。
