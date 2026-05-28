# W3 spec: 写 5 个 subagent + `/ship` slash command + PostToolUse hook(只接 gate.py)

> **wave**:W3
> **状态**:✅ done(2026-05-27)
> **subagent 已用**:verify `a1ed44b6d6247fa9c`(ALL PASS)+ reviewer `a314f9896446dd863`(REVISE→P0)→ 复查 `aee417a5d8487beb7`(P0 闭合 ship)+ Musk `abbb9cef176af51ad`(合规)
> **W3 主体**:主线程单写者(§4.0 决策)
> **基线**:`b2998df`(W2 方法论回灌完工状态)
> **用户决策(2026-05-27)**:① hook 三层只接 `gate.py`,另两层(`validate_run_log.py` / `ship_complete_check.py`)留 W4 ② 后续按主线程推荐执行,不逐项确认

---

## 0. 设计依据(出处,反 speculation)

| 决策 | 出处 |
|---|---|
| 5 个 subagent 清单 + 四件套 prompt | `docs/ARCH_REFACTOR_V1_PLAN.md` A2(L147-165)+ Multi-agent Research System |
| `/ship` slash command 显式触发 | A5(L235-237)+ 官方 issue #19308「prompt 强制约束 broken,要 hook/slash/subagent 确定性」 |
| hook 三层结构 + exit code 语义 | A5(L239-267) |
| **hook 只接 gate.py** | 用户决策(2026-05-27)+ invariant #4「0 消费者=0 生产」:`validate_run_log.py` / `ship_complete_check.py` 是 W4(invocation log)产物,现不存在,不先布死引用 |
| subagent **薄壳委托**(不重新内嵌 skill 逻辑) | invariant #2「统一语言:同一物理目的只一个组件」;writer/critic/cover 逻辑已在 user-level skill |
| 业务输出 JSON(verdict)定在 W3,invocation.json 防伪元数据留 W4 | A2(业务产物)vs A3(防伪/哈希/时间戳)分层 |
| critic verdict 字段 + source pattern | `tools/critic_vote.py`(B=ship/no-ship/skip,C=sign/no-sign/skip)+ `tools/gate.py` `REQUIRED_SOURCE_PATTERNS` |

---

## 1. 物理目的(一句话)

把「靠 SKILL.md 里 prompt 喊 BLOCKING REQUIREMENT / 条件触发」换成「**显式 `/ship` slash + 5 个 context 隔离的 subagent + 1 个 PreToolUse hook**」的确定性约束,堵官方 issue #19308 的根因(Claude 系统性忽略 prompt 层硬约束)。

**W3 是纯新增基础设施** — 只建 `.claude/` 下的 agent / command / hook 文件,**不改 critic/lint/gate 逻辑,不动 SKILL.md / WRITE_AGENT.md**。subagent 用薄壳委托现有 skill,不重写业务逻辑。§8.7 文档同步矩阵**无触发**(没改 critic/lint/skill/gate);但新 artifact 内容必须描述 **W2 后现状**(双轨 B+C / 无 Track A / 隐藏天花板 force_ship / 零人工 gate)。

---

## 2. 改动文件清单(全部新建,0 修改)

### 2.1 新建 5 个 subagent(`.claude/agents/`)

每个 frontmatter 四件套(`name` / `description` / `model` / `tools`)+ 正文四段(objective + output format + tool guidance + task boundary)。

| 文件 | 阶段 | model | 委托 skill | 业务输出 |
|---|---|---|---|---|
| `fengyun-iti.md` | Stage 1 Collect | sonnet | fengyun-writer(200 字试稿)+ content-judge(D-1 dogfood) | `output/research/<date>-<slug>.md` |
| `fengyun-writer.md` | Stage 2 Write | opus | **fengyun-writer skill**(完整稿) | `output/drafts/<date>-<slug>-v{N}.md` |
| `fengyun-critic-huashu.md` | Stage 3 Track B | sonnet | **huashu-perspective skill** | `output/verdicts/<slug>_huashu.json` |
| `fengyun-critic-content-judge.md` | Stage 3 Track C | sonnet | **content-judge skill** | `output/verdicts/<slug>_content_judge.json` |
| `fengyun-cover.md` | Stage 4 Publish | sonnet | **huashu-image-curator skill** Mode 2 | cover png + 内文图 png + metadata |

**model 依据**(memory `feedback_use_sonnet_for_agents`:默认 Sonnet,重创作/开发→Opus):writer 写 4000-5000 字创作 = opus;iti(调研)/critic(应用 skill rubric 出 binary)/cover(工具编排 + curator skill 做重活)= sonnet。

### 2.2 新建 `/ship` slash command(`.claude/commands/ship.md`)

- frontmatter:`description` + `argument-hint`
- `$ARGUMENTS` = 主题(留空 → ITI 数据驱动选题)
- 正文:**确定性编排** 4 阶段 → 顺序 dispatch 5 个 subagent,Stage 3 两个 critic **并行**,跑 `critic_vote.py` + revise loop,Stage 4 cover 后跑 `post_fengyun_publish.py`(触发 gate.py hook)。引用 `SKILL.md` / `WRITE_AGENT.md` 做详细 SOP + 不变量。

### 2.3 新建 hook 配置(`.claude/settings.json`)

**只接 1 层**(用户决策):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [ { "type": "command", "command": "python tools/gate.py" } ]
      }
    ]
  }
}
```

- `gate.py` 已是 hook-ready:读 stdin payload,**只在命令含 `post_fengyun_publish` 时**跑 frontmatter 检查 + `exit 2` 阻断,其余 Bash 一律 `return 0` 放行(主线程已读 `tools/gate.py` L428-462 确认)。
- **W4 待接两层**(本 wave 不写,settings.json 保持纯净无死引用):
  - `PostToolUse`(`Write|Edit|MultiEdit`)→ `tools/validate_run_log.py`(W4 invocation log 建后接)
  - `Stop` → `tools/ship_complete_check.py`(W4 建后接)
- exit code 语义(A5):`0` 通过 / `2`+stderr 阻断 / `1` warning。

### 2.4 不改动(明确边界)

`SKILL.md` / `WRITE_AGENT.md` / `tools/*.py` / `references/*` 一律不动。W3 不做 SKILL→subagent 的 dispatch 重写(那是 W5/W6 ship.py SDK 编排范围)。

---

## 3. 改前 vs 改后(对照样例)

### 改前(约束靠 SKILL.md prompt 喊,issue #19308 会被忽略)

```markdown
## Stage 2 / 4 · Write
调 fengyun-writer skill 写 4000-5000 字（不许主线程手写）。
```
→ 实测主线程会「假装写文章」绕过(gate.py 注释 Round 22 P0-6 记录的踩坑)。

### 改后(`.claude/agents/fengyun-writer.md` — 独立 context subagent,薄壳委托)

```markdown
---
name: fengyun-writer
description: Stage 2 Write。把研究材料写成 4000-5000 字完整稿，必须真调 fengyun-writer skill 注入风云 voice。
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep, Skill
---

## Objective
给定 output/research/<slug>.md，产出 output/drafts/<slug>-v{N}.md ...

## Output format
... frontmatter 含 writer_pass/title_pass/ending_pass + *_real_run + *_source ...

## Tool guidance
1. 真调 fengyun-writer skill（不许自己手写正文）...
2. python tools/title_signal.py / ending_signal.py ...

## Task boundary
只写不评（critic 是 fengyun-critic-* subagent）；改稿只动局部不重写全文。
```

---

## 4. 执行步骤(主线程严格按顺序)

### 4.0 执行模式决策:W3 主体用主线程单写者(不 fan-out)

§8 禁令 #9 **允许** W3 fan-out,但不是强制。本 wave 选**主线程单写者**,理由:
1. 5 个文件共享强约定(输出路径 / 四件套结构 / 委托 pattern / W2 后现状描述),单写者保证一致性,正是 §0 W3「reviewer 收尾审一致性」想防的漂移。
2. §11 单写者铁律:`arch-refactor-v1` 同树只能一个写者;Agent subagent 并行写主树 = race,安全 fan-out 只有 `git worktree`,对 5 个小文件过重。
3. Jobs 砍刀:5 个小配置文件并行成 5 个 session 是 process-theater,收益≈0,风险>0。

**fan-out 仍保留为能力**(W7 等大文件可用);W3 主动放弃。

### 4.1 建目录 + 写 5 个 subagent

```bash
mkdir -p .claude/agents .claude/commands
```
按 §2.1 逐个写,四件套 + 四段正文。

### 4.2 写 `/ship` slash command(§2.2)

### 4.3 写 `.claude/settings.json`(§2.3,只接 gate.py)

### 4.4 收尾自检(主线程先跑,reviewer 会复查)

```bash
# JSON 合法
python -X utf8 -c "import json;json.load(open('.claude/settings.json',encoding='utf-8'));print('settings.json OK')"
# 5 subagent + 1 command 齐
ls .claude/agents/*.md ; ls .claude/commands/*.md
# 每个 subagent frontmatter 四件套齐
grep -lE "^name:" .claude/agents/*.md | wc -l
```

---

## 5. 验收命令(W3 专有,verify subagent 跑;sandbox 限制时主线程兜底)

### 5.1 通用基线(每 wave 必跑)

```bash
python -X utf8 scripts/verify_baseline.py
```
期望:**121 passed / 0 deselected**(W2 后基线;W3 没动 tools/ 应零回归)。

### 5.2 W3 专有验收

```bash
# 1. 文件齐:5 subagent + 1 command + 1 settings
test $(ls .claude/agents/*.md 2>/dev/null | wc -l) -eq 5 || echo "FAIL: agents != 5"
test -f .claude/commands/ship.md || echo "FAIL: ship.md missing"
test -f .claude/settings.json || echo "FAIL: settings.json missing"

# 2. 每个 subagent 四件套齐(name/description/model/tools)
for f in .claude/agents/*.md; do
  for k in name description model tools; do
    grep -qE "^$k:" "$f" || echo "FAIL: $f 缺 frontmatter $k"
  done
done

# 3. 四段正文齐(objective/output/tool/boundary 语义段)
for f in .claude/agents/*.md; do
  grep -qiE "objective|目的"   "$f" || echo "FAIL: $f 缺 objective"
  grep -qiE "output|输出"      "$f" || echo "FAIL: $f 缺 output format"
  grep -qiE "tool|工具|命令"   "$f" || echo "FAIL: $f 缺 tool guidance"
  grep -qiE "boundary|边界|不做" "$f" || echo "FAIL: $f 缺 task boundary"
done

# 4. settings.json 合法 + 只有 PreToolUse 一层 + 指向 gate.py
python -X utf8 -c "
import json
s=json.load(open('.claude/settings.json',encoding='utf-8'))
h=s['hooks']
assert list(h.keys())==['PreToolUse'], h.keys()
assert 'gate.py' in h['PreToolUse'][0]['hooks'][0]['command']
assert 'PostToolUse' not in h and 'Stop' not in h, 'W4 层不该在 W3 出现'
print('settings.json 结构 OK — 只接 gate.py')
"

# 5. critic subagent 的 source 描述满足 gate.py pattern(防 W4 接 audit 时不匹配)
grep -qE "ship|verdict|灵魂" .claude/agents/fengyun-critic-huashu.md || echo "FAIL: huashu source pattern"
grep -qE "挂名|verdict|ship" .claude/agents/fengyun-critic-content-judge.md || echo "FAIL: content-judge source pattern"
grep -qE "huashu-image-curator Mode 2" .claude/agents/fengyun-cover.md || echo "FAIL: cover curator source pattern"

# 6. 无死引用:W3 不该提到 W4 才有的脚本作为「已接 hook」
grep -RnE "validate_run_log|ship_complete_check" .claude/settings.json && echo "FAIL: settings.json 含 W4 死引用" || echo "OK: 无 W4 死引用"
```

---

## 6. 风险 + 兜底(W3 专有)

### 6.1 gate.py 当 PreToolUse Bash hook 误伤普通命令
**风险**:hook 在每个 Bash call 前跑 gate.py,若 gate.py 对非 publish 命令也 exit 2,整个 pipeline(乃至本次重构的所有 Bash)被卡死。
**兜底(已验证排除)**:主线程已读 `tools/gate.py` `extract_from_stdin_hook_payload()`(L428-462)——仅当 `"post_fengyun_publish" in cmd` 才 check,否则 `return None, False` → `main()` `return 0` 放行。verify §5.2 不直接测 hook 行为(无法在静态轨触发),但 reviewer 会复读这段确认。

### 6.2 subagent / skill 名字冲突
**风险**:subagent `fengyun-writer` 与 skill `fengyun-writer` 同名,调用时歧义。
**兜底**:agent 与 skill 是不同命名空间(`.claude/agents/` vs `~/.claude/skills/`)。subagent 正文 Tool guidance 明确「调 fengyun-writer **skill**」,描述里写清是 Stage-Write 编排壳。reviewer 判断是否需改名(本 wave 遵循 A2 原名)。

### 6.3 subagent 描述与 W2 后现状漂移
**风险**:subagent 写成旧三轨 / 提 Track A score_draft / 写「人工 gate」。
**兜底**:critic subagent 只写双轨 B+C;cover/critic 不提数字分;全程零人工 gate;评委 subagent prompt **永不出现「轮次/上限」**(隐藏天花板在 critic_vote.py 代码层)。reviewer + Musk 双查。

### 6.4 settings.json 被 Claude Code 拒绝解析
**风险**:hook schema 写错(漏 `type: command`)导致 settings.json 无效。
**兜底**:用官方 schema(`type`+`command`);§5.2 #4 用 json.load + 断言结构。

---

## 7. reviewer subagent prompt(全新 session 审 W3 收尾)

```
你是 W3 reviewer subagent — 全新 session,read-only。审 W3「写 5 subagent + /ship slash + PreToolUse hook(只接 gate.py)」的产物 + spec。

读:
1. refactor_specs/wave_03_subagents_slash_hook.md(本 spec,看「应该是什么样」)
2. .claude/agents/*.md(5 个 subagent)
3. .claude/commands/ship.md
4. .claude/settings.json
5. 对照 tools/critic_vote.py + tools/gate.py(verdict 字段 / source pattern 是否对得上)
6. ~/.claude/skills/fengyun-publish/SKILL.md(4 阶段是否一致)

审 6 维度:
1. 5 subagent 四件套(name/description/model/tools)+ 四段正文(objective/output/tool/boundary)齐?
2. 薄壳委托?(writer/critic/cover 是调 skill 而非重写逻辑)
3. 与 W2 后现状一致?(双轨 B+C / 无 Track A / 无人工 gate / 评委不提轮次)
4. critic verdict 字段对得上 critic_vote.py?source 描述满足 gate.py REQUIRED_SOURCE_PATTERNS?
5. settings.json 只接 gate.py、无 W4 死引用、schema 合法?
6. /ship 编排顺序对?(iti→writer→[B‖C 并行]→critic_vote+revise loop→cover→post)

binary verdict: ship / revise / major issue。不通过列具体文件+行号+问题+建议。
报告 ≤ 1500 字,不许 emoji 不许时间预估。
```

---

## 8. Musk 监督员 prompt(全新 session 审 W3 过程合规)

```
你是 Musk 监督员 — 全新 session。先读 elon-musk-perspective skill,再读 REFACTOR_PLAN.md + refactor_specs/wave_03_subagents_slash_hook.md。
跑 git log/diff 看 W3 实际执行轨迹。

5 维核验(§8.5.1):
Q1 Idiot Index: W3 该多简单 vs 实际?(纯新增 7 个文件,不该有冗余 commit/反复)
Q2 诚实程度: commit message + spec 跟实际改动对得上?hook 真只接了 gate.py 还是偷偷塞了别的?
Q3 学习闭环: 守住「先派 subagent 再开工」了吗?(W3 主体单写者是 spec §4.0 写明的合规决策,不是偷懒省 subagent)
Q4 invariant #4「0 消费者=0 生产」: 有没有接 validate_run_log/ship_complete_check 这种「脚本还没有就先布 hook」的假承诺?(应该没有)
Q5 subagent 真用 vs 假用: 收尾 verify/reviewer/Musk 三 agent 真派了吗?

binary verdict: 合规 / 偏离。给 W3 一句话告诫 + W4 监督建议。
```

---

## 9. W3 完工标准

全部满足才能 commit:

- [ ] `.claude/agents/` 5 个 subagent(四件套 + 四段正文)
- [ ] `.claude/commands/ship.md`
- [ ] `.claude/settings.json`(只接 gate.py,无 W4 死引用,schema 合法)
- [ ] §5.2 W3 专有验收全 PASS
- [ ] verify subagent(静态轨)+ 主线程兜底(动态轨 `verify_baseline.py` 121 passed)
- [ ] reviewer subagent verdict: ship
- [ ] Musk 监督员 verdict: 合规
- [ ] REFACTOR_PLAN.md §0 W3 行 🚧 → ✅ + §11 handoff 刷新

---

## 10. 下一步执行清单(主线程严格按序)

1. ✅ 写 wave_03 spec(本文件)
2. ✅ REFACTOR_PLAN.md §0 W3 行 ⏸ → 🚧
3. ✅ 建 `.claude/agents` + `.claude/commands`,写 5 subagent
4. ✅ 写 `/ship` slash command
5. ✅ 写 `.claude/settings.json`(只接 gate.py)
6. ✅ 主线程收尾自检(§4.4)+ 动态轨 verify_baseline 121 passed
7. ✅ verify subagent `a1ed44b6d6247fa9c` ALL PASS + 主线程动态轨兜底
8. ✅ reviewer subagent `a314f9896446dd863` REVISE→抓 P0(critic source 未回填)→ 当轮修 → 复查 `aee417a5d8487beb7` P0 闭合 ship
9. ✅ Musk 监督员 `abbb9cef176af51ad` 合规(Idiot Index ≈ 1×,11 工具实测全存在)
10. ✅ 三者全过 → commit + REFACTOR_PLAN §0/§4.3/§11 更新 ✅
