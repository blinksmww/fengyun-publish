# Stage 4 Publish — 详细 SOP

> 主体跳转:`SKILL.md` Stage 4 / 4 · Publish
> 跨阶段约束:见主体「关键不变量」段(image_paths 非空 / cover_path 物理存在 / huashu 配图决策真 invoke)
> 本文件来源:SKILL.md.pre-w1-bak L1011-1369,W1 纯拆分不改字段
>
> **⚠️ W4(2026-05-27)**:`cover_pass`/`huashu_decision_pass`/`huashu_image_curator_*` 已迁 invocation log。
> cover 阶段跑完写 `cover.invocation.json`(`--input-file` = 当前 draft,`--result covered`);推草稿成功后写 `render.invocation.json`。
> **`image_paths`/`cover_path`/`image_at_h2_indices` 仍留 frontmatter**(物理产物指针,spec §1.1)。
> gate 推草稿前查 6 件 pre-publish invocation 齐全 + 物理图存在。下文 frontmatter pass_flag 写法是 W4 前历史描述 —— 以本 banner + `frontmatter_checklist.md` 为准。

---

## Step 7 · 出封面(W7 重写 2026-05-27,无模板)

> **W7(2026-05-27)取代旧 7 模板路由 + cover_dedup**:封面改成**无模板** — 花叔 cover mode 读这一篇文章自著**中文** Seedream prompt。`tools/generate_cover_by_template.py` + `tools/cover_dedup.py` 已物理删除。

**主力工具**:`tools/seedream_client.py`(薄客户端,豆包 Seedream 5.0 火山引擎方舟;prompt 透传,无模板 replace)+ `huashu-image-curator` **Mode 3 cover**(花叔自著中文 prompt)。

### 无模板流程(一句话)

花叔读文章自著中文 prompt(Style Block 锁品牌色 + 手绘 + 无人物 + ≤3 元素,**无签名**)→ `seedream_client.py` 透传出图;标题走**模型内渲染**(轻量中文指令,不再 5 层英文加固)。权威 Style Block 见 `D:\Dev\ai-wechat-pipeline\COVER_STYLE_GUIDE.md`,cover mode 引用它做单一真源。

### 调用方式(三步)

**① 抽 title/subtitle**(≤14/≤22 截断,Seedream 渲染稳定性):
```bash
# seedream_client 提供 extract_title_subtitle;或直接从 draft frontmatter 抽干净纯标题
python tools/seedream_client.py --help   # 查 CLI
```

**② 调 `huashu-image-curator` Mode 3 cover**(主线程 invoke skill,真调,gate 审计):传 `article_md + title + subtitle`(已截断)→ 花叔输出 JSON:
```json
{
  "prompt": "横幅 16:9,手绘 sketchnote 风格封面。暖米 #F8F0E0 纸纹底,陶土橙 #D97757 为唯一彩色线条…<主体 metaphor 由花叔按内容写>…标题「<TITLE>」清晰准确渲染,副标「<SUBTITLE>」。≤3 个主视觉元素,主体突出,留白足够缩略图清晰。",
  "aspect": "16:9",
  "style_anchor": "warm sketchnote hand-drawn, cream paper #F8F0E0, terracotta #D97757 accent line, editorial illustration",
  "metaphor_note": "一句话:为什么这个视觉最能表达这篇 + 骗点击"
}
```

**③ `seedream_client.py` 透传出图**(retry ×3 指数退避 1/2/4s + placeholder fallback 全内藏):
```bash
python tools/seedream_client.py \
    --prompt "<花叔的中文 prompt>" \
    --aspect <16:9|2.35:1> \
    --out output/images/YYYYMMDD-<slug>-cover.png \
    --style-anchor "<style_anchor>"
```

输出:`output/images/YYYYMMDD-<slug>-cover.png` + sidecar `<cover>.style_anchor.txt`(从 `--style-anchor` 写,供 Step 7.2 内文图 Mode 2 复用,**无签名**)。

### 工具优先级链

| 层级 | 工具 | 触发条件 |
|---|---|---|
| **主力 + retry ×3** | `huashu-image-curator` Mode 3 cover 自著中文 prompt → `tools/seedream_client.py`(豆包 Seedream,火山引擎方舟,.env 已配 `VOLCENGINE_IMAGE_KEY`;retry ×3 指数退避 + placeholder fallback 内藏)| 默认 |
| **应急** | 风云手工写 prompt + `--seed N` 重跑 | retry 全失败仍想调 |
| **兜底** | `baoyu-cover-image` skill / `assets/placeholder-sketch.png` placeholder(seedream_client 内藏) | 国内 API 全挂 |

### 风格识别度(每张封面必含)

1. 暖米 `#F8F0E0` 底(纸纹)
2. 陶土橙 `#D97757`(唯一彩色)
3. 手绘 sketchnote 风格
**(W7 删云签名)** — 品牌色 + 手绘风保留,缩略图零识别的「云」签名已删。

### 标题渲染(模型内,轻量中文指令)

标题文字交给 Seedream 模型内渲染(Phase 7 实测中文渲字 100%),prompt 里只用**轻量中文指令**(「标题『<TITLE>』清晰准确渲染」),**不再用 5 层英文加固**(已删)。

##### → 立即写入 frontmatter(Step 7-cover 封面生成完成后)

```yaml
cover_pass: true
cover_path: output/images/YYYYMMDD-<slug>-cover.png
```

> W4 banner:`cover_pass` 已迁 invocation log(以本文件顶部 W4 banner + `frontmatter_checklist.md` 为准);`cover_path` 仍留 frontmatter(物理产物指针)。本 W7 只改 cover **生成方式**(无模板),不碰 frontmatter 字段迁移。

封面文件必须物理存在。写完才进 Step 7.1-7.3 内文图。

## Step 7.1-7.3 · 内文图体系(Round 9 重设计,2026-05-24)

**核心架构**:封面跟内文图**完全独立** — 封面走上面无模板花叔 cover mode 自著 prompt 体系(W7),内文图走花叔 Mode 2 决策 + AI 生成体系。

**Round 9 用户 3 个决策**:
1. **R20 图密度不拦截** —「没图片的文章不一定不是好文章」,lint 改 info-only(已落地)
2. **图片用 AI 生成 only** — 联网搜图剔出 pipeline(真照片 / 产品截图 / 数据图表 → 作者手动塞 escape hatch)
3. **不蒸馏新 skill,用花叔做配图决策** — fork 成 `huashu-image-curator`(已落地),不污染原 huashu-perspective

**Musk × Jobs Round 4-5 共识**:
- 函数选候选位置 + skill 一次 LLM call 决策全篇(不是每张 1 call)
- 数量由花叔决定(0-5 张,**允许 0 张**)
- 篇内 style_anchor 一致 / 篇间自由
- skill 内置 self-check(灵魂红线),不外加 critic 步骤

### 调用方式(三步)

**Step 7.1: 函数预筛候选位置**(无 LLM 调用)
```bash
python tools/illustrate_decider.py output/drafts/YYYYMMDD-<slug>-v0.md --dry-run
```
- `--dry-run` 跑 `read_article_meta` + `pick_candidates`,打印候选位置(每个含 h2_idx / h2_title / position_idx / paragraph_preview / word_count),不调 LLM 不出图

**Step 7.2: invoke `huashu-image-curator` skill Mode 2**(Claude 主线程 invoke)

⚠️ **Round 21 决策 2:封面 + 内文图风格统一** —
Step 7-cover(封面)已经先于 Step 7.2 跑过,生成的封面对应 sidecar 文件 `<cover-image>.style_anchor.txt`,**必须读出来作为 style_anchor 输入传给花叔**,确保篇内封面 + 内文图风格一致。

```bash
# Step 7-cover 生成的 sidecar;内容作 huashu Mode 2 的 style_anchor 输入(不存在则 null)
cat output/images/<slug>-cover.style_anchor.txt
```

```
用 huashu-image-curator Mode 2 配图决策:
  - 文章: <article_md 全文>
  - 候选位置: <pick_candidates 返回的 list>
  - style_anchor: <cover_style_anchor>(Round 21:必须传封面 anchor,不再 null)

输出 JSON {should_illustrate, count: 0-5, image_at_h2_indices, style_anchor, positions, prompts, alts, self_check}
```

**关键**:花叔在 Mode 2 输出里的 `style_anchor` 字段必须等于或扩展自 `cover_style_anchor`(基底:warm sketchnote / cream paper #F8F0E0 / terracotta #D97757 accent / no human face / editorial illustration;**W7 删 cloud signature**),不允许另起炉灶。

**Bug 2 闭环 2026-05-24 Round 10**:JSON 必含 `image_at_h2_indices` 字段(slot 编号列表,0=intro hero / 1=H2[0] / ...)。illustrate_decider.write_metadata() 把这个字段写到 frontmatter,Step 8 post_fengyun_publish 读取后透传给 layout_rules,实现「花叔指定的图章节号 ↔ 渲染层」闭环。

**Step 7.3: 调火山 Seedream 出图 + 写 metadata**

先把 Step 7.2 花叔返回的 decision JSON 写到 `output/runs/<slug>/image_decision.json`,再出图(真 CLI `illustrate_decider --generate`:内部走 generate_from_decision(max_workers=3, retry_failed=True)+ write_metadata):
```bash
python tools/illustrate_decider.py --draft output/drafts/YYYYMMDD-<slug>-v0.md --generate --decision output/runs/<slug>/image_decision.json --slug <slug>
```

如果 `decision["should_illustrate"] == false` → `image_paths = []`,**继续 Step 8 推草稿**(0 张图合法 ship)。

##### → 立即写入 frontmatter(Step 7.2 配图决策完成后)

```yaml
huashu_decision_pass: true
huashu_image_curator_real_run: true
huashu_image_curator_source: "huashu-image-curator Mode 2, count=3, style=warm sketchnote"
image_at_h2_indices:
  - 0
  - 2
  - 4
```

4 个字段(含 image_at_h2_indices list)。写完才进 Step 7.3 出图。

### post_fengyun_publish.py 自动 inline

扫 `output/images/<slug>-NN.png` 按命名顺序拼到对应 H2 之后(`layout_rules.render_to_wechat_html` 的 `section_image_urls` 参数已支持)。命名规则跟 illustrate_decider.py 写出来的一致:`<slug>-01.png / 02.png / ...`。

### 失败回退链(Round 9 简化)

1. **huashu-image-curator skill 不存在** → 跳过 Step 7.2 - 7.3,0 张图 ship,run log `degraded.illustration = "skill missing"`
2. **skill 返回非 JSON / 解析失败** → 0 张图 ship,run log `degraded.illustration = "decision parse fail"`
3. **火山 Seedream API 失败** → retry × 1(已有逻辑)→ 仍失败 → 0 张图 ship(部分失败的图 ship 已成功的)+ run log 标记
4. **不再有「手动选图补救」步骤** —「允许 0 张图」已经覆盖这个 case

### 数据飞轮 v1 metadata

每次配图决策后,illustrate_decider.write_metadata() 自动把以下字段写到 draft frontmatter:

```yaml
illustrate_anchor: warm reflective editorial illustration
illustrate_count: 3
illustrate_should: true
images:
  - path: output/images/<slug>-01.png
    alt: "20-40 字中文 alt 文本"
    h2: "他的转身"
  - path: output/images/<slug>-02.png
    alt: "..."
    h2: "他在算的那笔账"
```

**30 天后回看**:聚合多篇文章 illustrate_anchor 分布,被动观察「研究 Agent 的云」长期视觉 IP 的潜在归纳。不主动约束,只观察。

### 真实素材 escape hatch(不入代码 pipeline)

什么时候作者(风云)手动塞真实素材而不走 AI 生成:
- 讲**特定人物**时放真照片(如 Karpathy 头像)
- 讲**产品发布**时放官方截图(如 Claude 4.7 新功能截图)
- 讲**数据**时放原始图表(如 Anthropic 财报折线图)

操作:在 draft markdown 里手动插入 `![alt](path)`,illustrate_decider 不会覆盖已有的 inline 图。AI 生成层只补「概念性 / 情绪性 / 抽象 sketch」类的图。

### 为什么从 Round 5 P0 强制改成 Round 9 灵活

Round 5 P0「每 1100 字 1 张强制」基于 PHASE1_FACTS 对标号数据(卡兹克 / 宝玉爆款规律)。Round 9 用户原话「没图片的文章不一定不是好文章」推翻强制,改为:
- **被动观察**(数据飞轮记录 anchor / count,30 天后回看)
- **主动决策**(花叔基于灵魂判断 + 选题胆量 + build-what-you-use,允许 0-5 张)
- **R20 lint 改 info-only**(不阻断不警告)

成本 vs 收益:Idiot Index < 1(每篇花叔决策 1 次 LLM call ≈ ¥0.05 + 出图 0-5 张 × ¥0.2 = ¥0-1/篇)。比强制 5 张更省 + 比强制 0 张更对场景。

## Step 8 · 排版 + 推草稿

```
python tools/post_fengyun_publish.py output/drafts/YYYYMMDD-<slug>-v0.md
```

`post_fengyun_publish.py` 是从 `post_fengyun_v3.py` 通用化来的:
- 接受 `DRAFT_PATH` 命令行参数
- 自动按 `YYYYMMDD-<slug>-cover.*` 找封面
- 内文图可选(`--insert TRIGGER=PATH=ALT` 多次)
- frontmatter 抽 title / digest / author / style / theme / article_type / **image_at_h2_indices**(Bug 2 闭环)
- **渲染走 `tools/layout_rules.py`**,**Round 10 起默认 huashu T-A 暖米黄风格**(2026-05-24)
- image_at_h2_indices 从 frontmatter 读取后透传 layout_rules,**花叔决定的图章节号 ↔ 渲染层真正闭环**
- 渲染成微信 HTML,先写本地 preview(`output/html/`),再上传 thumb + 创建 draft
- 返回 `media_id`(草稿 ID)

### 渲染模式(2026-05-25 Round 21 决策 1:huashu 锁死为唯一活跃路径)

**Round 21 决策 1.1+1.2 锁定** — 排版统一花叔,legacy renderer 和 default/classic 分支已物理砍掉:

| 历史模式 | 现状 |
|---|---|
| `--render-mode layout_rules`(原默认) | **已不需要传**,argparse 中 `--render-mode` 选项已删 |
| `--render-mode legacy` | ❌ **已砍**(post_fengyun_publish.py 删了 `_render_html_legacy` 函数 + 6 个硬编 style 常量) |
| `style=default / classic` | ❌ **已砍**(layout_rules.py 删了 78 行 default 分支 + 13 个 default-only helper) |
| `style=huashu`(任何值或不传) | ✅ **唯一活跃路径**,所有渲染都走 huashu T-A |

**为什么砍**:用户决策(2026-05-25)「排版统一用花叔那个,其他的那些所谓排版都删了」。
**lint HTML 上限**:Round 21 P0-17 抬到 60000 字节(原 20000 是 layout_rules 内部历史值,无外部出处;微信真实物理上限 ~65000)。
**huashu 模板路径**:`D:\Dev\ai-wechat-pipeline\tools\layout_rules_huashu.yaml`

**详细规则**:`D:\Dev\ai-wechat-pipeline\tools\layout_rules.py` 的 `LAYOUT_RULES` dict
**完整落地文档**:`D:\Dev\ai-wechat-pipeline\docs\LAYOUT_RULES_ROUND3.md`
**lint 自检**:render 后自动跑,有违规打 WARN 到 run log(不阻断,不等人工 — 推草稿后风云在草稿箱审阅时一并看)

### Style 分支(2026-05-24 Round 5,跟 --render-mode 正交)

writer 在 frontmatter 写 `style: huashu` → 整个流程**自动**走花叔风格,**无需 CLI 参数**。

| frontmatter | layout 渲染 | lint 触发 |
|---|---|---|
| 无 `style` 字段(默认) | `LAYOUT_RULES` 9 维度(风云本人风格) | R0-R18 |
| `style: huashu` + `theme: A` | `layout_rules_huashu.yaml` template_A(暖橙) | R0-R18 + R19_huashu - R27_huashu |
| `style: huashu` + `theme: B` | `layout_rules_huashu.yaml` template_B(深红) | 同上 |

**huashu 触发的 9 条额外 lint**(`fengyun_lint.py` 自动按 frontmatter.style 决定是否跑):
- `R19_huashu_avg_para_length` warn — 平均段长 50-80
- `R20_huashu_solo_lines` warn — 独段成行 ≥ 4 处
- `R21_huashu_h2_pattern` warn — H2 命中 3 种模式之一
- `R22_huashu_emoji_zero` **error** — emoji = 0(必改)
- `R23_huashu_cta_zero` **error** — 零 CTA / 零二维码(必改)
- `R24_huashu_long_para_ratio` warn — >200 字段落 ≤ 8%
- `R25_huashu_ellipsis` warn — 省略号 ≤ 1 处
- `R26_huashu_bold_per_para` **medium**(Round 23 新增) — **每段 bold ≤ 1 处** — Musk × Jobs 共识:单段 spotlight 1 chunk
- `R27_huashu_bold_total` **medium**(Round 23 新增) — **全文 bold ≤ 5 处**(短文 < 1000 字 ≤ 3) — 物理依据:working memory 4±1

**回滚**:writer 不写 `style` 字段即回退默认行为,零影响。
**完整规则源**:`D:\Dev\ai-wechat-pipeline\tools\layout_rules_huashu.yaml`
**辩论 + 6 份调研证据**:`D:\Dev\ai-wechat-pipeline\reports\huashu_layout_phase1\`

成功:输出 `output/runs/YYYYMMDD-<slug>.json`,包含 `draft_media_id`。
失败(网络 / token / quota):**留本地 HTML preview + ERROR 日志**,**本轮不重试**(外部失败 pipeline 内无法自愈),cron 下轮自动重跑,无人工。

## Step 9 · 返回报告(必须 print 给用户)

最后一步,把全流程结果汇总打出来:

```
=== fengyun-publish ship 报告 ===
主题: <title>
slug: <slug>
北极星: <填空>

草稿 ID: <draft_media_id>(aborted_r18 时为空,pipeline 自动终止未推草稿,无人工)
选用版本: <v0 / v1 / v2 ...>(末轮)

critic 双轨(末轮,W2.C6 删 Track A):
  B · huashu:       <ship/reject/skip+降级原因>
  C · content-judge: <挂名/不挂名/skip+降级原因>
  决议(gate tree): <ship / force_ship / aborted_r18>
  决议理由: <gate_tree reason>

force_ship: <true / false>
  (true = 改稿到隐藏天花板仍未双过,代码层强制 ship + WARN 标记;
   数据飞轮统计 force_ship 比例,过高 = writer 或评委阈值要调)

R18 触发情况:
  P0(明确自指 AI 身份):     <n 处 / 0>
  P1(架构/skill/工具栈暴露): <n 处 / 0>
  P2(自动化流程暴露):       <n 处 / 0>
  (r18_dashboard.py 周报会监控阈值:P1>2 / P2>3 告警)

机械 lint: 0 violations(末轮,不含 R18-P1/P2 计入统计的 hits)
改稿轮数: <n>
总用时: <分钟>

下一步(按决议分,全流程无人工交互):
  ship → 推草稿箱 → 风云草稿箱审阅 + 发出(pipeline 外,唯一人工动作)
  force_ship → 同 ship 推草稿(已标记 force_ship,风云审阅时留意)
  aborted_r18 → pipeline 自动终止(改到天花板仍自爆 AI),ERROR 日志,未推草稿,无人工;cron 下轮选别的主题
```

并把 JSON 版本写到 `output/runs/YYYYMMDD-<slug>.json` 留档。
