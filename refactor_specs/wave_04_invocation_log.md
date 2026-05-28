# W4 spec: 31 frontmatter 防伪字段 → invocation log（gate.py 改写为消费者）

> **wave**:W4
> **状态**:✅ done（2026-05-27）
> **subagent**:调研 `a4dbcf0bf952be555` + verify `a48e760129a0952ed`（ALL PASS / 139+30）+ reviewer `a03ea81bae8f08a64`（REVISE → P1:WRITE_AGENT per-step 缺 banner → §总览加全局 banner）+ Musk `abea887cf76b5c66f`（合规，Idiot Index ≈ 1.3×）
> **基线**:`cbdb6ad`（W3 完工状态）
> **执行模式**:单写者，test-first，绝不 fan-out（schema + gate.py 强一致，§8 禁令 #9）

---

## 0. 设计依据（出处，反 speculation）

| 决策 | 出处 |
|---|---|
| invocation log 6 文件 + JSON schema 字段 | `docs/ARCH_REFACTOR_V1_PLAN.md` A3（L167-206） |
| gate.py = invocation log 的**第一个真消费者**，同 wave 落地 | invariant #4「0 消费者=0 生产」+ Musk W4 预警（REFACTOR_PLAN §11） |
| frontmatter 回归 metadata | invariant #3（REFACTOR_PLAN §1.1 #3）|
| **scope 切分:pipeline-state 防伪字段迁走，article-metadata + 物理指针留下** | 见 §1.1 —— invariant #5「真公理优先」+ Newton「物理文件检查是真 invariant」+ Jobs 砍刀（避免 render/publish 级联）|
| input_hash 匹配 = 反 fake 升级 | A3 schema `input_hash` + Newton「真 invariant 优先」:frontmatter pass_flag 证明不了「critic 跑的是最终稿」，hash 匹配能 |
| 2 个延后 hook（validate_run_log / ship_complete_check）在 W4 接 | W3 spec §2.3 + A5 |
| 调研 map（字段全集 / 生产者 / 测试覆盖 / 下游引用面）| 调研 subagent `a4dbcf0bf952be555` |

---

## 1. 物理目的（一句话）

把 `gate.py` 当前强制的 ~25 个 **pipeline-state 防伪字段**（`*_pass` / `*_real_run` / `*_source`）从 draft frontmatter 迁到 `output/runs/<slug>/*.invocation.json` invocation log，**gate.py 改写为 invocation log 的消费者**（检查文件存在 + schema 合法 + `input_hash` 匹配当前稿 + `finished_at` < 1h + critic 决议 ∈ {ship, force_ship}）。frontmatter 回归「文章 metadata + 物理产物指针」。

**这是 Newton 式 invariant 升级**:旧 frontmatter `critic_b_pass: true` 证明不了「critic 评的是最终稿」（改完 draft 旗标还在）；`input_hash == sha256(当前稿)` 能证明「这一轨真的在这一版上跑过」。反 fake 从「字段在不在」升级到「跑的是不是这一版」。

### 1.1 ⚠️ scope 切分决策（Jobs 砍刀 + invariant #5，主线程拍板，记录备查）

A3/invariant #3 字面是「frontmatter 回归 title/digest/author/north_star」。但调研 map 显示 `image_paths` / `cover_path` / `image_at_h2_indices` 是**物理产物指针**:`illustrate_decider.py::write_metadata()` 写入、`post_fengyun_publish.py` 读取渲染、`test_gate_image_mandatory.py` 12 个测试覆盖。

**切分**:
- **迁走（pipeline-state 防伪字段，hypothesis-non-fingo 材料）**:所有 `*_pass` / `*_real_run` / `*_source`（writer/title/ending/lint/wangxiaobo/critic_b/critic_c/critic_vote/huashu_decision/huashu_image_curator/cover_pass）→ invocation log。
- **留在 frontmatter（文章 metadata + 真物理 invariant，Newton:物理文件检查是真公理不是 fake-pass 猜想）**:`title` / `digest` / `author` / `slug` / `date` / `north_star` / `style` / `theme` / `article_type` / `image_paths` / `cover_path` / `image_at_h2_indices`。gate.py **保留**对 image_paths/cover_path 的物理存在 + size≥5KB 检查 + `aborted_r18` 检查。

**理由**:① image_paths 是「文章有哪些图」= article metadata，不是 pipeline state，留 frontmatter 合 invariant #3 精神；② gate 对它的检查是真物理 invariant（文件在不在 + 够不够大），不是「你有没有真调 skill」的 fake-pass 猜想；③ 迁它会级联 illustrate_decider + post_fengyun_publish + 渲染路径 = 超出 W4 blast radius，留到 W6(ship.py)/W7(cover) 触渲染时再议。**W4 砍掉这个级联,只做防伪字段迁移。**

---

## 2. 改动文件清单

### 2.1 新建（5 个）

| 文件 | 作用 | 行数预估 |
|---|---|---|
| `assets/run_log.schema.json` | invocation.json 的 JSON Schema（强制结构）| ~50 |
| `tools/invocation_log.py` | 生产者 + 校验器:`write_invocation()` 写一个 `<stage>.invocation.json`（含 sha256 input_hash）+ `validate_invocation()` + `load_run()` + CLI | ~160 |
| `tools/validate_run_log.py` | **PostToolUse hook**:Write/Edit 写了 `*.invocation.json` → 按 schema 校验，非法 exit 2 | ~70 |
| `tools/ship_complete_check.py` | **Stop hook**:session 停止时核验当前 run 的必需 invocation 集齐全 + decision ∈ {ship,force_ship}，缺 exit 2 | ~90 |
| `tools/test_invocation_log.py` | **test-first**:schema 校验 / write→load round-trip / hash 匹配 / 过期(>1h) / 缺文件 / decision 校验 | ~140 |

### 2.2 修改（代码，3 个）

| 文件 | 改动 |
|---|---|
| `tools/gate.py` | 删 `REQUIRED_PASS_FLAGS` / `REQUIRED_AUDIT_FIELDS` / `REQUIRED_SKILL_AUDIT_FIELDS` / `REQUIRED_SOURCE_PATTERNS` / `REQUIRED_EVIDENCE_FIELDS` 的 frontmatter 检查;新增 `REQUIRED_INVOCATIONS` + `check_invocations(slug, draft)`。**保留**:base 字段存在性、image_paths/cover_path 物理检查、image_at_h2_indices 存在、aborted_r18、force-skip-gate、audit log、stdin hook dispatcher。 |
| `.claude/settings.json` | 加 PostToolUse(`Write\|Edit\|MultiEdit`)→ `validate_run_log.py` + Stop → `ship_complete_check.py`（W3 延后的两层）|
| `tools/test_gate_image_mandatory.py` | `_make_draft` fixture 去掉迁走的 25 个字段（只留 metadata + image），新增「同 slug 下造 6 个合法 invocation.json」的 fixture helper，使 12 个 image 测试在新 gate 下仍 PASS |

### 2.3 invocation log 文件集（6 个 pre-publish，gate.py 检查；render 由 Stop hook 检查）

`output/runs/<slug>/`:

| 文件 | 生产者（subagent/orchestrator）| 取代的旧字段 | result 取值 |
|---|---|---|---|
| `iti.invocation.json` | fengyun-iti | （collect 真跑）| `collected` |
| `writer.invocation.json` | fengyun-writer | writer/title/ending `*_pass`+`*_real_run`+`*_source` | `written` |
| `verify.invocation.json` | 主线程 Stage 3（lint + 王小波 + vote）| lint_pass / wangxiaobo_* / critic_vote_pass/revise_loop_pass/force_ship | `ship`\|`revise`\|`force_ship` |
| `critic_b_huashu.invocation.json` | fengyun-critic-huashu | critic_b_real_run/source | `ship`\|`no-ship`\|`skip` |
| `critic_c_content_judge.invocation.json` | fengyun-critic-content-judge | critic_c_real_run/source | `sign`\|`no-sign`\|`skip` |
| `cover.invocation.json` | fengyun-cover | cover_pass / huashu_decision_pass / huashu_image_curator_* | `covered` |
| `render.invocation.json` | post 渲染后（Stop hook 查）| —（新）| `rendered` |

**schema 字段**（A3 + stage/result/draft_path 扩展）:
```json
{
  "stage": "writer",
  "skill_name": "fengyun-writer",
  "started_at": "ISO8601",
  "finished_at": "ISO8601",
  "version": "v1.x",
  "round": 1,
  "input_hash": "sha256:<当前 draft 文本 hash>",
  "output_files": ["output/drafts/..."],
  "result": "written",
  "summary": "..."
}
```

### 2.4 文档同步（§8.7 矩阵，改 gate/防伪逻辑必连带）

| 文件 | 改动 |
|---|---|
| `WRITE_AGENT.md` | Step 8（L826-918）gate 字段清单改为「写 invocation log（invocation_log.py）+ gate 查 invocation 集」;各 Step 的 `*_pass` 示例改为「跑完调 invocation_log.py 写 `<stage>.invocation.json`」 |
| `~/.claude/skills/fengyun-publish/references/frontmatter_checklist.md` | 大改:frontmatter 只剩 metadata + image 清单;新增 invocation log 段（6 文件 + schema 链 run_log.schema.json）|
| `~/.claude/skills/fengyun-publish/SKILL.md` + `references/stage_02/03/04.md` | pass_flag 描述改为 invocation log;关键不变量段加「invocation log 是 ship 凭证」|
| `vendor/skills/fengyun-publish/`（§8.6）| 同步上述 user-level 改动（cp -r）+ 顺手修 stage_04_publish.md L182 过时 `image_paths = []` |
| `.claude/agents/*.md` + `.claude/commands/ship.md` | 各 subagent output 加「跑完写 `<stage>.invocation.json`」;/ship 各 stage 后调 invocation_log.py;删 Step 4.5 的 critic source 回填（改为 critic subagent 写 critic_b/c invocation.json）|
| `scripts/verify_baseline.py` | 加第 3 件:invocation log schema 自检（A3 承诺「W4 完工后扩展」）|
| `README.md` / `CHANGELOG.md` | image_paths 仍在 frontmatter（不变）;补 invocation log 架构一句话 |

---

## 3. 改前 vs 改后

### 改前（gate.py 查 frontmatter 25 个防伪字段）
```python
REQUIRED_AUDIT_FIELDS = [("critic_b_real_run","critic_b_source",...), ...]
# draft frontmatter 必须有 critic_b_real_run: true + critic_b_source: "..."
# 问题:改完 draft v3，v1 的旗标还在 → 证明不了 critic 评的是 v3
```

### 改后（gate.py 查 invocation log）
```python
REQUIRED_INVOCATIONS = ["iti","writer","verify","critic_b_huashu","critic_c_content_judge","cover"]
# output/runs/<slug>/critic_b_huashu.invocation.json:
#   存在 + schema 合法 + input_hash == sha256(当前 draft) + finished_at < 1h
# verify.invocation.json result ∈ {ship, force_ship} 才放行
```

---

## 4. 执行步骤（主线程单写者，严格 test-first）

1. **先写 schema + test**（plan「schema 测试脚本先写」）:`assets/run_log.schema.json` + `tools/test_invocation_log.py`（此时 invocation_log.py 还没写，测试应 import fail / red）
2. 写 `tools/invocation_log.py` → 跑 test_invocation_log 到 green
3. 改 `tools/gate.py`:加 `check_invocations`，删 frontmatter 防伪检查，保留物理/base/r18
4. 改 `tools/test_gate_image_mandatory.py` fixture（造 invocation.json）→ 跑到 green
5. 写 `tools/validate_run_log.py` + `tools/ship_complete_check.py`（hook 入口，stdin payload 解析比照 gate.py）
6. 改 `.claude/settings.json` 加两层
7. `scripts/verify_baseline.py` 加 invocation schema 自检
8. 文档同步（§2.4 全清单）+ vendor cp -r + grep 旧术语确认无活引用
9. 收尾自检 → verify subagent（静态轨）+ 主线程动态轨 `verify_baseline.py` → reviewer → Musk → commit

---

## 5. 验收命令（W4 专有）

```bash
# 通用基线（gate.py 重构后必须仍绿）
python -X utf8 scripts/verify_baseline.py      # 期望 ≥121 passed（含新 test_invocation_log）

# W4 专有
python -X utf8 -m pytest tools/test_invocation_log.py -q
python -X utf8 -m pytest tools/test_gate_image_mandatory.py -q
# schema 合法
python -X utf8 -c "import json;json.load(open('assets/run_log.schema.json',encoding='utf-8'));print('schema OK')"
# hook 脚本可独立跑（非 publish 命令应 exit 0 放行）
echo '{}' | python -X utf8 tools/validate_run_log.py; echo "validate exit=$?"
# settings.json 现在三层齐
python -X utf8 -c "import json;h=json.load(open('.claude/settings.json',encoding='utf-8'))['hooks'];print(sorted(h.keys()))"  # ['PostToolUse','PreToolUse','Stop']
# 旧防伪术语在 gate.py 已无活引用（只剩注释/superseded）
grep -nE "REQUIRED_AUDIT_FIELDS|REQUIRED_SKILL_AUDIT_FIELDS" tools/gate.py || echo "OK: 旧常量已删"
```

---

## 6. 风险 + 兜底

### 6.1 gate.py 是 ship 安全网,改坏 = 假稿能 ship 或真稿 ship 不了
**兜底**:test-first;`test_gate_image_mandatory.py` 12 测试 + 新 `test_invocation_log.py` 全绿才算;reviewer 全新 session 重点审 check_invocations 逻辑;**保留 force-skip-gate 兜底通道**。

### 6.2 input_hash 匹配跨 stage 不一致（iti/writer 在 draft 定稿前跑）
**兜底**:gate 只对**操作最终稿的 stage**（verify/critic_b/critic_c/cover）强制 `input_hash == sha256(当前 draft)`;iti/writer 只查存在 + schema + finished_at recent（它们的 input_hash 是 research/前一版，不强制等于当前稿）。schema 里 input_hash 必填但 gate 分级校验。

### 6.3 文档同步漏 WRITE_AGENT.md（W2 踩过的坑，§8.7）
**兜底**:§2.4 列全;收尾 `grep -rn "critic_b_real_run\|writer_pass\|REQUIRED_AUDIT" WRITE_AGENT.md tools/ ~/.claude/skills/ vendor/` 确认只剩 superseded 标注;reviewer 专项查 WRITE_AGENT。

### 6.4 旧 draft（output/drafts/3 个）带旧 frontmatter
**兜底**:新 gate **忽略**多余 frontmatter 字段（不报错），旧 draft 不需迁移;新 ship 用精简 frontmatter + invocation log。向后兼容,零破坏。

### 6.5 scope 切分被质疑（image_paths 没迁是否违 invariant #3）
**兜底**:§1.1 已记录理由（物理指针 = 真 invariant + article metadata + 避级联）。reviewer/Musk 若判定必须迁，记 P0 当轮议;否则按 §1.1 接受。

---

## 7. reviewer subagent prompt（全新 session 审 W4 收尾）

```
你是 arch-refactor-v1 W4 reviewer — 全新 session,read-only,不知主线程怎么写的。项目根 D:\Dev\ai-wechat-pipeline\。
W4:把 gate.py 的 ~25 个 frontmatter 防伪字段迁到 output/runs/<slug>/*.invocation.json,gate.py 改写为消费者。image_paths/cover_path 物理指针按 spec §1.1 故意留在 frontmatter。

读:refactor_specs/wave_04_invocation_log.md(spec)、assets/run_log.schema.json、tools/invocation_log.py、tools/gate.py(改后)、tools/validate_run_log.py、tools/ship_complete_check.py、tools/test_invocation_log.py、tools/test_gate_image_mandatory.py、.claude/settings.json、WRITE_AGENT.md(Step 8)、~/.claude/skills/fengyun-publish/references/frontmatter_checklist.md。

审:
1. gate.py check_invocations 逻辑对吗?input_hash 分级校验(最终稿 stage 强制匹配,iti/writer 宽松)合理吗?有没有让假稿能 ship 的洞?
2. 旧防伪 frontmatter 检查真删干净了?force-skip-gate / image 物理检查 / r18 / base 字段 / audit log 保留了吗?
3. invocation_log.py schema 与 run_log.schema.json 一致?write→load round-trip + hash 正确?
4. 两个 hook 脚本 stdin dispatcher 像 gate.py 一样「非目标命令放行」,不会误伤普通 Write/Stop?
5. settings.json 三层 schema 合法?
6. §8.7 同步:WRITE_AGENT.md Step 8 / frontmatter_checklist.md / SKILL+refs+vendor 真追平?grep 旧字段名无活引用?
7. scope §1.1(image_paths 留 frontmatter)你认不认?认就说,不认列 P0。
8. test_gate_image_mandatory.py 12 测试 + test_invocation_log.py 是否真覆盖、真绿?

binary:ship / revise / major issue。列文件+行号。≤1800 字,无 emoji,无时间预估。
```

---

## 8. Musk 监督员 prompt（全新 session 审 W4 过程）

```
你是 arch-refactor-v1 W4 Musk 监督员 — 全新 session。先加载 elon-musk-perspective skill。读 REFACTOR_PLAN.md(§1.1 invariant / §8 / §8.5.1 / §8.7 / §11 的 W4 预警) + refactor_specs/wave_04_invocation_log.md。跑 git log/diff 看 W4 轨迹(W4 未 commit 看工作树)。

按 §8.5.1 答 5 问:
Q1 Idiot Index:W4 该多大 vs 实际?有没有过度工程化(invocation 文件数/字段)?spec §1.1 砍掉 image 级联是聪明砍还是漏做?
Q2 诚实:spec 跟实际代码对得上?gate.py 真删了旧检查还是留了死代码?
Q3 学习闭环:test-first 真做了(schema+test 先写)?守住单写者不 fan-out?
Q4 ⭐invariant #4(W4 的核心红线):invocation log 的真消费者(gate.py 改写 + validate_run_log + ship_complete_check)是不是**和 schema 同 wave 落地**?有没有「先建 schema、消费者等 W6」?这是你 W3 收尾留给 W4 的专项预警,重点查。
Q5 subagent 真用:收尾 verify/reviewer/Musk 三 agent 真派?

binary:合规 / 偏离。给 W5 监督建议。≤1500 字,无 emoji,无时间预估。
```

---

## 9. W4 完工标准

- [ ] `assets/run_log.schema.json` + `tools/invocation_log.py` + 两个 hook 脚本
- [ ] `tools/gate.py` 改写(查 invocation log,删旧防伪 frontmatter 检查,留物理/base/r18)
- [ ] `tools/test_invocation_log.py` + 改后 `test_gate_image_mandatory.py` 全绿
- [ ] `.claude/settings.json` 三层(W3 两层延后接上)
- [ ] `scripts/verify_baseline.py` 加 invocation schema 自检
- [ ] §8.7 文档同步全清单 + vendor + grep 无旧字段活引用
- [ ] verify(静态+动态)+ reviewer ship + Musk 合规
- [ ] REFACTOR_PLAN §0 W4 ✅ + §4.4 完工记录 + §11 handoff(下一 wave = W5)

---

## 10. 下一步执行清单

1. ✅ 写 wave_04 spec(本文件)
2. ✅ REFACTOR_PLAN §0 W4 ⏸ → 🚧
3. ⬜ schema + test_invocation_log(test-first,red)
4. ⬜ invocation_log.py → green
5. ⬜ gate.py 改写 + test_gate fixture → green
6. ⬜ validate_run_log.py + ship_complete_check.py
7. ⬜ settings.json 三层 + verify_baseline 扩展
8. ⬜ §8.7 文档同步 + vendor + grep 自检
9. ⬜ verify + reviewer + Musk
10. ⬜ 三过 → commit + REFACTOR_PLAN §0/§4.4/§11 ✅
