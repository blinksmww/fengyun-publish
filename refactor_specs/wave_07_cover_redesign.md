# Wave 7: Cover 系统重做 — 无模板 AI 自著 prompt

> **状态**:🚧 open(2026-05-27)
> **取代**:`docs/ARCH_REFACTOR_V1_PLAN.md` §阶段 D 的「单模板 T5 + 随机 seed」前提 —— 用户 2026-05-27 拍板改为**无模板**(AI 读文章自著 prompt),比单模板砍得更彻底。
> **决策依据**:用户拍板(视觉设计决策,人定不是 AI 定)+ Musk 第一性原理 verdict + 两轮调研(内部可复用零件 + 外部约束边界最佳实践,均有出处)。

---

## 物理目的(一句话)

把封面从「7 固定模板 + 关键词路由 + 写死英文 prompt + 7 天 dedup」换成「**花叔 cover mode 读文章自著中文 Seedream prompt**(结构化自由:Style Block 锁品牌色+手绘风,主体 metaphor 放给 AI)→ **薄客户端 `seedream_client.py` 出图**(retry+placeholder 全内藏)」;**物理删**模板+dedup,删云签名+5 层英文加固。

---

## 决策锁定(用户 2026-05-27 逐条拍板)

| 维度 | 决定 |
|---|---|
| **模板** | ❌ 无模板。AI 读这一篇自己定 metaphor + 写 prompt |
| **谁写 prompt** | `huashu-image-curator` 新增 **cover mode**(花叔 taste,跟他已经在写的内文图 Mode 2 同一套眼睛 + style_anchor 衔接)。责任方仍是 `fengyun-cover` subagent |
| **删(物理删,不归档)** | `cover_dedup.py` 整个删;`generate_cover_by_template.py` 整个删(名字=by_template,无模板后作废);云签名;5 层英文加固 |
| **留(Style Block 锁)** | 品牌色 `#F8F0E0` 暖米底 + `#D97757` 陶土橙(唯一彩)+ 手绘 sketch-notes 风格 |
| **Prompt 语言** | 中文(Seedream 5.0 中文原生优化,官方双语定位);build 时中英各 3 张 **A/B 实测**验证不劣化 |
| **标题文字** | 模型内渲染(Seedream 中文渲字是强项,Phase 7 实测 100%);用**轻量中文渲染指令**,不要 5 层英文加固 |
| **参考图** | W7 不上,纯文本 Style Block(hex 锁色,外部证据 ★★★★);留后续 wave |
| **字段骨架** | 结构化自由:cover mode 输出固定字段,只有「主体 metaphor + 情绪」随文章变,其余锁死 |
| **回滚** | git tag `backup-pre-refactor-20260526` + 每 commit `git revert` + `vendor/` 镜像;**不靠 `archived/`**(archived 跟 git 重复,Musk「the best part is no part」) |

---

## 改动文件清单(精确到行号)

### A. 物理删除(2 个文件整删)

| 文件 | 行数 | 理由 | 安全性 |
|---|---|---|---|
| `tools/cover_dedup.py` | 304 | 无模板就无「撞型」概念;品牌色+AI 自然变化负责区分 | 唯一消费者是 `generate_cover_by_template.py`(L567),一起删;**无 test 引用**(20 test 文件无 cover 测试) |
| `tools/generate_cover_by_template.py` | 647 | 文件身份=按模板生成;无模板后整个作废 | 有用零件迁 `seedream_client.py`(见 C);**无 test 引用** |

> ⚠️ 执行时先确认 `opening_dedup.py` 对 cover_dedup 不是反向 import(grep 命中疑似注释,非依赖)。

### B. 新建 — `tools/seedream_client.py`(薄客户端)+ 测试

**`tools/seedream_client.py`**(test-first):
- `generate_cover(prompt, aspect, out_path, seed=None, style_anchor=None) -> dict`
  - ARK 调用迁自 `generate_cover_by_template.py:_call_seedream_once`(L406-445),**但 prompt 直接透传不再 `.replace` 模板**(L412 那行删)
  - retry 迁自 `generate_image`(L448-492),**改 ×2 固定 2s → ×3 指数退避 1/2/4s**(对齐 Round 25 `feedback_round25_image_mandatory`)
  - **新增 placeholder fallback**:全失败 → 复制 `assets/placeholder-sketch.png` 到 out_path(现状只打印提示无 fallback;Round 25 硬约束要求)
  - sidecar 写出迁自 L631-637,**去掉「soft cloud signature」那句**(签名已删);anchor 从 `--style-anchor` 入参写,不再硬编
- `extract_title_subtitle(draft_path)` 迁自 L366-400(保留 ≤14/≤22 截断,Seedream 渲染稳定性)
- argparse CLI:`--prompt`(必需)`--aspect` `--out` `--title` `--subtitle` `--seed` `--style-anchor`
- **0 改业务**:不带 `TEMPLATES` / `classify` / `CATEGORY_RULES` / `read_routing_text` / dedup gate

**`tools/test_seedream_client.py`**(先写跑挂 → 实现 → 跑过):
1. `extract_title_subtitle` 截断(>14→13+…,>22→20+…)
2. placeholder fallback:mock ARK 抛异常 ×3 → out_path 落 placeholder + size ≥ 5KB
3. retry 指数退避序列:mock 失败,断言 sleep 调用 1/2/4(不真调网络)
4. prompt 透传:`--prompt "X"` 原样进 payload(不再有模板 replace)

### C. 改写(skill / agent / 宪法 / 文档)

| 文件 | 改动 |
|---|---|
| `~/.claude/skills/huashu-image-curator/SKILL.md` | **新增 Mode 3: cover**(Mode 2 之后)。触发=「封面 prompt」/被 `fengyun-cover` 调。输入 `article_md + title + subtitle`(已截断)。五步迁移花叔模型(emotion=这篇核心→选题胆量=metaphor 不俗套→build-what-you-use=风云会用这张?→aspect 决策→写**中文** prompt)。**Style Block 锁**(暖米#F8F0E0底+陶土橙#D97757唯一彩+手绘sketchnote+无人物+≤3视觉元素+缩略图友好,**无云签名**)。输出 JSON `{prompt(中文), aspect, style_anchor, metaphor_note}`。3-5 条**中文 few-shot**(旧 7 模板 metaphor 改写)。**轻量中文标题渲染指令**(不要 5 层英文加固)。frontmatter description 加 cover mode 触发词 |
| `.claude/agents/fengyun-cover.md` | Stage 4 cover 流程改写:删「7 模板路由 + cover_dedup」(L40, L42-45);新流程 ① 读 draft 抽 title/subtitle ② 调 huashu cover mode → 中文 prompt+aspect+style_anchor ③ `python tools/seedream_client.py --prompt ...` 出图 ④ sidecar(供内文图)⑤ 内文图路径(illustrate_decider + Mode 2)**不变**。invocation summary 改「huashu cover mode + seedream_client」 |
| `~/.claude/skills/fengyun-publish/references/stage_04_publish.md` | Step 7 重写(L14-128):删 7 模板矩阵(L39-51)/英文加固 5 层(L59-68)/路由规则(L89-97)/dedup gate(L99-119);三件套(L79-83)**去云签名**。改为无模板 cover mode 流程 + Style Block + 中文 prompt + 轻量标题 + seedream_client 调用。工具优先级链(L71-78)保留(主力 Seedream→应急手工→兜底 baoyu/placeholder) |
| `~/.claude/skills/fengyun-publish/SKILL.md` | 骨架 cover 命令 `generate_cover_by_template.py` → cover mode + `seedream_client.py` |
| `WRITE_AGENT.md`(repo 根,**§8.7 最易漏**) | 宪法 cover/Step 对应段同步:无模板 / 去签名 / 去英文加固 |
| `COVER_STYLE_GUIDE.md` | 砍掉死的 5/7 模板 prompt 段(已与代码分叉),slim 成**权威 Style Block**(品牌色+手绘+**无签名**+缩略图规则);cover mode 引用它做单一真源 |
| `vendor/skills/fengyun-publish/` | 镜像 `SKILL.md` + `references/stage_04_publish.md`(§8.6) |
| `vendor/skills/huashu-image-curator/`(**新增镜像**) | W7 改了 huashu-image-curator(user-level,原不在 git)→ 扩展 §8.6 加此镜像保 rollback 安全 |

### D. 已知 stale,**不在 W7 scope**(reviewer 别误判漏改)

- `docs/*.md` 历史报告(SYSTEM_AUDIT / DEAD_CODE_SCAN / phase* / BRAND_STRATEGY / HUASHU_DEFAULT 等)= 日期快照,不改
- `README.md` / `docs/architecture*.svg` / `diagram/`、`output/diagrams/` SVG = 架构图,重画成本高,defer 到 W10 / neat-freak
- `*.pre-w1-bak` = 备份,不改

---

## 改前 vs 改后(代码样例)

**改前**(`generate_cover_by_template.py:411-412`,模板 replace):
```python
tpl = TEMPLATES[template_id]
prompt = tpl["prompt"].replace("{TITLE}", title).replace("{SUBTITLE}", subtitle)
```

**改后**(`seedream_client.py`,prompt 透传 —— prompt 由花叔 cover mode 写好):
```python
def generate_cover(prompt, aspect, out_path, seed=None, style_anchor=None):
    payload = {"model": MODEL, "prompt": prompt, "size": "2K",
               "response_format": "url", "watermark": False}
    if seed is not None:
        payload["seed"] = int(seed)
    # retry ×3 指数退避(1/2/4s),全失败 → placeholder fallback
    # 成功 → 写 sidecar(style_anchor,无 cloud signature)
```

**cover mode JSON 输出**(花叔写的,中文 prompt):
```json
{
  "prompt": "横幅 16:9,手绘 sketchnote 风格封面。暖米 #F8F0E0 纸纹底,陶土橙 #D97757 为唯一彩色线条…<主体 metaphor 由花叔按内容写>…标题「<TITLE>」清晰准确渲染,副标「<SUBTITLE>」。≤3 个主视觉元素,主体突出,留白足够缩略图清晰。",
  "aspect": "16:9",
  "style_anchor": "warm sketchnote hand-drawn, cream paper #F8F0E0, terracotta #D97757 accent line, editorial illustration",
  "metaphor_note": "一句话:为什么这个视觉最能表达这篇 + 骗点击"
}
```

**fengyun-cover 流程改后**:
```
① 读 draft → extract_title_subtitle(≤14/≤22)
② 调 huashu-image-curator cover mode(传 article_md + title + subtitle)→ 得 prompt/aspect/style_anchor
③ python tools/seedream_client.py --prompt "<prompt>" --aspect <16:9|21:9> \
       --out output/images/<slug>-cover.png --style-anchor "<anchor>"
④ sidecar 已写 → 内文图 Mode 2 复用(篇内一致)
⑤ illustrate_decider + Mode 2 内文图(不变)
```

---

## 验收命令(W7 专有)

```bash
# 1. 零回归(cover 删除不影响,无 test 引用)
python -X utf8 scripts/verify_baseline.py            # 期望 ≥ 173 passed / 0 deselected

# 2. 新工具 test-first 全过
python -X utf8 -m pytest tools/test_seedream_client.py -q

# 3. CLI 不崩
python tools/seedream_client.py --help

# 4. 活引用归零(user-level + vendor)
grep -rn "generate_cover_by_template\|cover_dedup" SKILL/references/WRITE_AGENT  # 仅剩「已删」标注
grep -rn "云签名\|cloud signature\|soft cloud\|labeled 「云」" <cover 相关>      # = 0(历史报告除外)

# 5. vendor 镜像 byte-identical(fengyun-publish + huashu-image-curator)

# 6. build A/B(Musk:别信,生成看):同 1 篇,中文 prompt vs 旧英文 各 3 张 → 人工确认中文不劣化
# 7. 物理 smoke:真跑一次 cover(或 mock 失败走 placeholder)→ 出图 size ≥ 5KB
```

---

## 风险 + 兜底

| 风险 | 兜底 |
|---|---|
| 中文 prompt 出图质量未验证 | build A/B 实测 gate;劣化 → 回英文(可逆,只改 cover mode prompt 一处) |
| 删 generate_cover_by_template 破坏调用链 | 全链路 grep + 真跑一次 ship cover step;改前先确认无反向 import |
| 花叔 cover mode 与 inline Mode 2 风格漂移 | style_anchor 衔接(cover mode emit → inline reuse),机制不变 |
| placeholder fallback 回归 | `test_seedream_client` 覆盖 + Round 25 硬约束(image_paths 非空 ≥5KB)保留 |
| huashu-image-curator 改动无 git 跟踪 | 新增 `vendor/skills/huashu-image-curator/` 镜像(扩展 §8.6) |
| ~~p-hacking / 盲推~~ | 不适用:W7 无阈值/词典改动(纯架构替换);无反复盲推 |

---

## reviewer subagent prompt(全新 session,审 diff + spec)

```
你是 fengyun-publish 重构 W7(cover 无模板重做)的 reviewer,全新 session 审 diff + spec,出 binary verdict(SHIP / REVISE)。读 refactor_specs/wave_07_cover_redesign.md + git diff。逐条核:
1. 业务逻辑 0 改:seedream_client 的 ARK 调用/retry/截断是从 generate_cover_by_template 迁移,不是重写打分/路由逻辑?prompt 是否真透传(无 TEMPLATES replace 残留)?
2. 物理删干净:cover_dedup.py + generate_cover_by_template.py 整删?无残留 import?无 test 因此挂?
3. Style Block 去签名:所有 cover 相关(skill/agent/stage_04/COVER_STYLE_GUIDE/WRITE_AGENT + vendor)的「云签名/cloud signature」是否清干净?品牌色 #F8F0E0/#D97757 + 手绘风是否保留?
4. 中文 prompt:cover mode 输出中文?5 层英文加固是否删?标题渲染指令是否轻量?
5. test-first:test_seedream_client 是否覆盖截断/placeholder/retry/透传?
6. doc-sync(§8.7):WRITE_AGENT.md(易漏)+ SKILL.md + stage_04 + vendor 双镜像(fengyun-publish + huashu-image-curator)是否都同步?
7. Round 25:placeholder fallback 是否真实装(≥5KB)?image_paths 非空约束是否保留?
8. scope:有没有动 inline 内文图路径(应不动)?有没有动无关业务?
P0 = 阻断(业务逻辑被改/删除残留导致崩/签名没删干净/中文 prompt 没落地);当轮修再 commit。
```
