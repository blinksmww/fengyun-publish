# Stage 2 Write — 详细 SOP

> 主体跳转:`SKILL.md` Stage 2 / 4 · Write
> 跨阶段约束:见主体「关键不变量」段(R18 红线 / image_paths 非空 / north_star 必填 / writer 真 invoke)
> 本文件来源:SKILL.md.pre-w1-bak L348-553,W1 纯拆分不改字段
>
> **⚠️ W4(2026-05-27)**:`writer_pass`/`title_pass`/`ending_pass` + `*_real_run`/`*_source` 已迁 invocation log。
> **⚠️ v2.0(2026-06-10)**:ending harness 已删、title harness 降档 advisory(依据见各 Step 段内)。
> 写完整稿 + 标题信号检查后写 `writer.invocation.json`
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

## Step 3.3 · 标题信号检查(v2.0 降档 ADVISORY,2026-06-10)

> **v2.0 降档依据**(`reports/dim_trigger_rate_audit_w9_after.json`,321 篇含卡兹克/宝玉/赛博禅心头部真品):
> W9 调参后头部真品 verdict pass 率仍仅 **32.7%** — 闸门把 67% 模仿对象判死 = 阈值体系无判别力;
> 真实发文 n=13 不足以校准。降为跑一次出参考信号,**不循环不阻断**。
> 等数据飞轮攒够真实打开率样本再校准回 BLOCKING(校准必须有独立科学动机,反 p-hacking)。
> 历史版(Round 16 harness 循环 + 评分维度表)见 git 历史或 `SKILL.md.pre-w1-bak`。

**执行(跑一次,不循环)**:

1. **评分 + 去重**(真 CLI;`<TITLE>`/`<e1>`/`<N>` 由主线程从 draft 填):
   ```bash
   # 评分:输出含 hook_type,供下一步 --hook-type <H>
   python tools/title_signal.py --title "<TITLE>" --topic-keywords <e1> <e2> --body-chars <N>
   # 去重:--draft 排除自身(Bug 4:不传必然 self-match Jaccard=1.0 撞型)
   python tools/title_dedup.py --title "<TITLE>" --hook-type <H> --max-age-days 14 --max-n-check 10 --draft output/drafts/<slug>-v0.md
   ```
2. 两个 JSON 输出**原样记入 run log**(数据飞轮校准材料)。
3. signal `verdict==fail` 或 dedup `is_too_similar==true` → 把 `redo_feedback` 给 `fengyun-writer`(改标题模式,**只改 frontmatter title,不改正文**)**一次**,writer 自主裁量改或不改;改完**不回评**,直接进 Step 4。
   - dedup 撞型信号参考价值最高(防 14 天内连续同型标题),writer 应优先采纳
4. `title_signal` / `title_dedup` 跑挂 → 跳过本 step,记 `degraded.title_check = "module fail"`,不阻断 ship。

**产物**:无独立 invocation,无 pass_flag;JSON 进 run log 即可。写完进 Step 4。

## Step 3.5 · (v2.0 已删:ending harness,2026-06-10)

**砍除依据**(`reports/dim_trigger_rate_audit_w9_after.json`,321 篇审计):
- 「末段 ≥150 字」hit 99.3% — 永不触发的死维度
- 「金句/摘要/召回密度 ≥6」三维 trigger 91.9-94.8% — 把 92-95% 头部真品判不合格
- 1 维永不响 + 3 维全员响 = 零判别力,这套阈值把模仿对象全体判死刑
- 原 PHASE1 4 信号(b_last_para_chars ρ=+0.300 等)是 critic 特征层相关性证据,不构成这套手写阈值的有效性证据

**结尾质量防线移交**:Step 5 王小波语感预审 + Stage 3 花叔 Track B(「愿你也能+颜文字」式公式收尾本就是花叔 emotion 维度毙稿点,实例:`output/verdicts/guizang-xhs-skill_huashu.json`)。

`ending_signal.py` / `ending_dedup.py` 保留在 tools/ 当审计仪器(`dim_trigger_rate_audit.py` 依赖),ship 流程不再调用。历史版设计见 git 历史或 `SKILL.md.pre-w1-bak`。

写完 Step 3.3 直接进 Step 4(详见 `references/stage_03_verify.md`)。
