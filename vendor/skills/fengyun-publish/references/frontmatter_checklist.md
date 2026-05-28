# Frontmatter Checklist + Invocation Log（W4 改版,2026-05-27）

> **W4(arch-refactor-v1,2026-05-27)大改**:pipeline-state 防伪字段(`*_pass` / `*_real_run` /
> `*_source`)全部从 frontmatter 迁到 `output/runs/<slug>/<stage>.invocation.json`。
> frontmatter 回归「文章 metadata + 物理产物指针」(invariant #3)。gate.py 改写为 invocation
> log 消费者。反 fake 升级(Newton):`input_hash == sha256(当前 draft)` 证明每一轨评的是这一版稿。
> 详见 `WRITE_AGENT.md` Step 8 + `tools/invocation_log.py` + `assets/run_log.schema.json`。
>
> **W2.C2 历史**:humanizer-zh 3 字段已删(改 fengyun_lint R29/R30)。**W2.C6**:Track A 数字分已删。

> 主体跳转:`SKILL.md` Stage X / 4 流程一览

---

## 一、frontmatter 字段(精简后只剩 metadata + 物理产物指针)

### Step 1.1 完成后(主线程写)
```yaml
slug: <slug>
date: <yyyy-mm-dd>
north_star: <北极星填空,< 30 字,是感受不是知识>
```

### Step 3 fengyun-writer 出稿后(只写 metadata,不再写 writer_pass 等)
```yaml
title: <title>          # ≤ 64 字
digest: <digest>
author: 研究Agent的云
style: huashu           # 可选,触发 huashu 渲染 + R19-R28 lint
theme: A                # 可选,huashu 模板 A 或 B
article_type: thought_essay  # 可选
```

### Step 7.3 出图后(illustrate_decider.write_metadata 自动写 — 物理产物指针,**留 frontmatter**)
```yaml
cover_path: output/images/YYYYMMDD-<slug>-cover.png
image_at_h2_indices: [0, 2, 4]        # 花叔 Mode 2 产物(空 list 允许)
image_paths:                           # 非空 + 每文件物理存在 + size ≥ 5 KB(Round 25 硬约束)
  - output/images/<slug>-01.png
  - output/images/<slug>-02.png
illustrate_anchor: warm reflective editorial illustration   # 数据飞轮
illustrate_count: 3
illustrate_should: true
images:
  - path: output/images/<slug>-01.png
    alt: "20-40 字中文 alt 文本"
    h2: "他的转身"
```

### R18 红线状态(命中才写)
```yaml
aborted_r18: true   # 命中 R18-P0 自动终止时写;gate 见此即阻断
```

**就这些。** 任何 `*_pass` / `*_real_run` / `*_source` / `critic_vote_pass` / `huashu_decision_pass` /
`cover_pass` / `force_ship` **不再写 frontmatter** —— 改写 invocation log(见下)。

---

## 二、invocation log(取代旧防伪字段;每 stage 跑完写一个)

路径 `output/runs/<slug>/<stage>.invocation.json`。写法:
```bash
python tools/invocation_log.py write \
    --slug <slug> --stage <stage> --skill <name> \
    --input-file <该 stage 的输入文件> --output <产物> \
    --result <result> --summary "<摘要>"
```

schema(`assets/run_log.schema.json`,10 字段):`stage` / `skill_name` / `started_at` /
`finished_at` / `version` / `round` / `input_hash`(sha256:64hex)/ `output_files` / `result` / `summary`。

### 6 件 pre-publish invocation(gate 推草稿前必查) + render

| stage | skill_name | `--input-file` | result | 取代的旧 frontmatter 字段 |
|---|---|---|---|---|
| `iti` | fengyun-iti | research | `collected` | (collect 真跑) |
| `writer` | fengyun-writer | research | `written` | writer/title/ending `*_pass`+`*_real_run`+`*_source` |
| `verify` | orchestrator | **当前 draft** | `ship`\|`force_ship`\|`revise` | lint_pass / wangxiaobo_* / critic_vote_pass / force_ship |
| `critic_b_huashu` | huashu-perspective | **当前 draft** | `ship`\|`no-ship`\|`skip` | critic_b_real_run / critic_b_source |
| `critic_c_content_judge` | content-judge | **当前 draft** | `sign`\|`no-sign`\|`skip` | critic_c_real_run / critic_c_source |
| `cover` | fengyun-cover | **当前 draft** | `covered` | cover_pass / huashu_decision_pass / huashu_image_curator_* |
| `render` | orchestrator | 当前 draft | `rendered` | (新;Stop hook 查完整性) |

### gate.py 校验铁律(`check_invocations`)
1. 6 件 pre-publish 齐全(缺一阻断)
2. 每件 schema 合法 + `finished_at` 距今 < 1h
3. **操作最终稿的 stage(verify / critic_b_huashu / critic_c_content_judge / cover)**:
   `input_hash == sha256(当前 draft)` —— 证明这一轨评的是这一版,不许拿旧版 verdict ship 新稿。
   改稿(v{N+1})后,这 4 件必须对新 draft 重写。
4. `verify.result` 必须 ∈ {`ship`, `force_ship`} 才放行(`revise` / `aborted_r18` 阻断)。

### 两个 hook(`.claude/settings.json`)
- **PostToolUse**(Write|Edit)→ `validate_run_log.py`:写出的 `*.invocation.json` schema 不合法 → exit 2
- **Stop** → `ship_complete_check.py`:run 缺 render(准备好没推)→ stderr WARN(咨询性,不阻断)

---

## 三、物理产物硬约束(留 frontmatter,gate 仍查)
- `image_paths` 非空 list,每文件物理存在 + size ≥ 5 KB。placeholder `assets/placeholder-sketch.png` 合法。
- `cover_path` 物理存在。

---

## 四、为什么这么改(invariant #3 + Newton)
- **invariant #3**:frontmatter 是文章 metadata,不是 pipeline state。`writer_pass: true` 是 pipeline state,该走 log。
- **Newton 真 invariant**:旧 `critic_b_pass: true` 改完稿旗标还在,证明不了「critic 评的是最终稿」;
  `input_hash` 匹配能。这是从「字段在不在」升级到「跑的是不是这一版」。
- **scope(spec §1.1)**:`image_paths` / `cover_path` 是物理产物指针(文件真存在是真 invariant),
  且属文章 metadata + 被渲染路径消费 → 留 frontmatter,不迁(避免级联 illustrate_decider / post_fengyun_publish)。
