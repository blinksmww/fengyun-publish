---
description: 风云 AI 公众号 end-to-end ship — 显式触发 4 阶段全自动流水线（Collect → Write → Verify → Publish）
argument-hint: [主题/事件，留空则 ITI 数据驱动选题]
---

# /ship — 风云公众号确定性发布流水线

显式触发本命令才跑（堵 LLM 自主挑省事路径，官方 issue #19308 根因）。工作目录 `D:\Dev\ai-wechat-pipeline\`。

**本次主题**:`$ARGUMENTS`
（为空 → Stage 1 走 ITI 数据驱动选题；非空 → 以该主题为 top_angle，仍跑 ITI 深搜补事实。）

详细 SOP 与不变量以 `~/.claude/skills/fengyun-publish/SKILL.md` + `WRITE_AGENT.md` 为准。本命令是**编排骨架**，每阶段 dispatch 对应 subagent，主线程只做汇总 + 决议 + 推送。

## ⛔ 全程不变量（每阶段都守）

- **north_star 必填**:Stage 1 不填「读者读完应该感受到 ___」不许进 Stage 2。
- **image_paths 非空**:Stage 4 每篇 ship ≥ 1 张图（placeholder 合法，size ≥ 5 KB）。
- **R18 红线**:R18-P0(明确自指 AI 身份)→ revise 自动删段；改到天花板仍 P0 → `aborted_r18` 自动终止(不 ship，无人工)。
- **零人工 gate**:全流程无人工交互，唯一人工 = 风云在草稿箱手动点发出。

## 编排流程

> **W4 invocation log（每阶段跑完必写,gate 的 ship 凭证）**:每个 stage 结束调
> `python tools/invocation_log.py write --slug <slug> --stage <stage> --skill <name> --input-file <file> --output <file> --result <result>`,
> 写 `output/runs/<slug>/<stage>.invocation.json`。gate.py 推草稿前查 6 件 pre-publish invocation
> 齐全 + schema 合法 + `input_hash` 匹配当前稿 + `finished_at`<1h + `verify.result`∈{ship,force_ship}。
> **取代旧的 frontmatter `*_pass`/`*_real_run`/`*_source` 防伪字段(W4 已从 gate 删除)。**

### Stage 1 / 4 · Collect
dispatch **`fengyun-iti`** subagent（传主题 `$ARGUMENTS`）。
拿回 `{slug, north_star, top_angle, fact_count, dogfood_passed}` + `output/research/<date>-<slug>.md`。
fengyun-iti 跑完写 `iti.invocation.json`（`--stage iti --skill fengyun-iti --input-file <research> --result collected`）。
dogfood 不过 → 让 fengyun-iti 换 top_angle 重选，仍不过则终止并报告。

### Stage 2 / 4 · Write
dispatch **`fengyun-writer`** subagent（传 research 路径）。
拿回 `output/drafts/<date>-<slug>-v0.md`（注入风云 voice + title/ending harness）。
fengyun-writer 跑完写 `writer.invocation.json`（`--stage writer --skill fengyun-writer --input-file <research> --output <draft> --result written`）。

### Stage 3 / 4 · Verify（lint → 王小波 → 双轨 critic → 投票）
1. `python tools/fengyun_lint.py <draft>` — 跑到 0 violation（R0-R30）
2. 调 `wangxiaobo-perspective` skill — 翻译腔预审
3. **双轨 critic 并行**：在**同一条消息里同时** dispatch `fengyun-critic-huashu`（Track B）+ `fengyun-critic-content-judge`（Track C）两个 subagent。⛔ 两轨 context 隔离，互不可见对方 verdict；评委 prompt 永不出现「轮次/上限」。
   - 各 critic subagent 跑完写自己的 invocation:`critic_b_huashu.invocation.json` / `critic_c_content_judge.invocation.json`,**`--input-file` = 当前 draft**(gate 要 input_hash 匹配最终稿),result = B 的 ship/no-ship、C 的 sign/no-sign。
4. 收齐 B/C 两个 verdict，组装 `rounds.json`（含 round / draft_path / b_verdict / c_verdict / lint_json_path）跑：
   `python tools/critic_vote.py --all-rounds <rounds.json> --out output/runs/<slug>/vote.json --verbose`
4.5 **写 `verify.invocation.json`（W4 — 取代旧 frontmatter 防伪字段回填）**：
   `python tools/invocation_log.py write --slug <slug> --stage verify --skill orchestrator --input-file <draft> --output <draft> --result <ship|revise|force_ship> --summary "lint=0 wangxiaobo=pass vote=<decision>"`
   - **`--input-file` 必须是当前 draft**(gate 校验 input_hash 匹配最终稿)。
   - result 取 critic_vote 决议:`ship`/`force_ship` 放行;`revise` 走改稿循环。
   - ⛔ 不再回填 `*_pass`/`*_real_run`/`*_source` 到 frontmatter(W4 已删 gate 对这些的检查)。
5. 按 decision 走（决议在 critic_vote.py 代码层，全自动）：
   - `ship` / `force_ship` → Stage 4
   - `revise` → 回 Stage 2 让 fengyun-writer 按 B/C 的 revise_targets 定向改稿（v{N+1}），**改稿后 verify/critic_b/critic_c/cover 必须对新 draft 重写 invocation**(input_hash 要跟新版匹配),重跑 Stage 3（评委不知有上限）
   - `aborted_r18` → 自动终止，ERROR 日志，**不 ship**，报告后结束

### Stage 4 / 4 · Publish
1. dispatch **`fengyun-cover`** subagent（传 ship 选中的 draft）→ 拿回 cover + image_paths + 花叔 Mode 2 metadata，写回 draft frontmatter（image_paths/cover_path/image_at_h2_indices 仍留 frontmatter）。cover subagent 跑完写 `cover.invocation.json`（`--stage cover --skill fengyun-cover --input-file <draft> --result covered`）。
2. `python tools/post_fengyun_publish.py <draft>` — 渲染 huashu layout + 上传草稿
   （此命令触发 `.claude/settings.json` 的 PreToolUse → `gate.py` 把关：**6 件 pre-publish invocation 齐全 + input_hash 匹配当前稿 + verify.result∈{ship,force_ship} + cover/image 物理存在**，缺一即 exit 2 阻断）
3. 推送成功后写 `render.invocation.json`（`--stage render --skill orchestrator --input-file <draft> --result rendered`）。
4. 推送失败(网络/token/quota)→ 留本地 HTML preview + 错误日志，不重试

### Step 9 · 报告
print 全流程结果（主题 / slug / 北极星 / 草稿 ID / B·C 末轮 verdict / 决议 / force_ship 标记 / R18 触发 / lint / 改稿轮数 / 下一步），并把 JSON 写 `output/runs/<date>-<slug>.json`。

## 唯一人工动作
公众号后台 → 草稿箱 → 看草稿 → 觉得 OK → 发出。其余全自动。
