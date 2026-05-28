# Wave 10: e2e 验收(跑完整 ship + 对标 §8 验收表 + A/B + 决定要不要替换主支)

> ⚠️ **本 wave 与 W1-W9 根本不同** —— **不是改代码的 wave,是验收 wave**:跑一次完整 /ship + 对标 ARCH §8 验收表 + 跟主支 A/B 对比质量 + 决定要不要整体替换主支。
> **最高风险动作 = 整体替换主支**(`git branch -M arch-refactor-v1 main`)。**这一步必须风云显式拍板,任何 agent / 主线程绝不许自动做。**
> 模式:**你 + verify + reviewer(全新 session)+ Musk(全程监督)**;§8.5 三 subagent 硬约束 + sandbox 双轨(§8.5.2)仍适用。
> ⚠️ **不报工时预估**(memory `feedback_no_time_estimates`):§8 表的「端到端耗时」降级为 advisory,不作硬验收门。

---

## 0. scope 来源 + 2 个 fork 拍板记录(2026-05-27)

W10 = ARCH_REFACTOR_V1_PLAN.md §6.2 W10 行 + §8 验收标准表。开工先派 1 个 Sonnet 只读 explorer 调研 e2e 现状(/ship 链路 / 凭证依赖 / §8 指标静态vs真跑 / 主支 diff / memory),再 AskUserQuestion 集中拍板:

| Fork | 调研发现 | 风云拍板 |
|---|---|---|
| **F1 e2e 真跑范围** | 主线程在风云本机,`.env` 有真 `VOLCENGINE_IMAGE_KEY` + `WECHAT_APPID/SECRET`,TrendRadar DB(`D:\Dev\TrendRadar\output\rss\2026-05-27.db` 1.27MB 今日已更新)+ aihot `?q=` 公开端点均可达 → 主线程能真跑完整 /ship 到草稿箱。sandbox 子 agent 跑不了任何真凭证步骤(HTTP 000 / 无本地FS / 无 .env)。 | **从零到一跑全流程**:真跑完整 /ship(Collect→Write→Verify→Cover→Publish),产真封面 + 真草稿,**推到「研究Agent的云」草稿箱**(花 Seedream + 微信 API 额度;风云草稿箱手动决定发不发)。这是验「gate 0 拦截 / lint ≤2 轮 / 信源 11进7+」的唯一真路径。 |
| **F2 A/B 老流程对照来源** | user-level `~/.claude/skills/fengyun-publish/SKILL.md` 已被 W1 替换成 199 行重构版(不随 git 分支变),重跑老流程要 `checkout main` + 临时恢复 1445 行旧 skill 到 user-level,污染共享 skill 且要还原,较脏。草稿箱已有 Round 17-25 老流程产物(v3/v4,05-21 anthropic-mythos)。 | **用草稿箱已有老稿对照**:拿草稿箱里已推的 v3/v4 老流程稿跟 W10 新流程稿并排比,不重跑老流程。**最终 A/B 质量结论 = 风云本人 founder verdict(主观),agent 不自动判**,只把两稿并排呈现 + 客观差异点列出。 |

---

## 1. 物理目的(一句话)

把 W0-W9 重构出来的新 pipeline 真跑一遍端到端,用 ARCH §8 验收表逐项核对「重构目标是否真达成」,跟主支老流程稿做质量 A/B,产出一个客观证据包供风云下「替不替换主支」的 go/no-go —— **本 wave 不改任何业务代码**(允许的写入仅:本 spec、REFACTOR_PLAN §0/§4.10/§11、可选的历史文档 cosmetic cleanup;以及 e2e 运行产生的 `output/` 运行时产物)。

---

## 2. §8 验收 checklist(8 项 + 回归基线)

来源:`docs/ARCH_REFACTOR_V1_PLAN.md` §8(行 568-582)。每项 → 静态测 or 真跑 e2e + 目标值 + pass 判据 + 验法。

| # | 指标 | 主支基线 | 目标 | 静态/真跑 | 验法 | pass 判据 |
|---|---|---|---|---|---|---|
| 1 | SKILL.md 行数 | 1480 | ≤300 | **静态** | `wc -l ~/.claude/skills/fengyun-publish/SKILL.md`(+ vendor 镜像) | ≤300 |
| 2 | Python 伪代码出现次数 | ~10 | 0 | **静态** | `grep -rn 'python -c'` + ` ```python ` 在 SKILL.md + references/ + WRITE_AGENT.md(user-level + vendor) | =0 |
| 3 | 三轨→双轨 critic 并行 | ❌串行 | ✅并行 | **静态+真跑** | 静态:ship.md「同一条消息同时 dispatch B‖C」;真跑:观察是否真并发 dispatch | spec 层并行 + 真跑观察到 B/C 同消息 dispatch |
| 4 | Cover 撞型 | 自动换模板 | 不会撞 | **静态** | W7 已物理删 `generate_cover_by_template.py` + `cover_dedup.py`,花叔 Mode3 每次自著 prompt + 随机 seed | 无模板路由代码;`fengyun-cover.md` 无模板调用 |
| 5 | 信源覆盖 | 11进3 | 11进7+ | **半静态+真跑** | W8 已实测 DB 257条/aihot 23条;真跑 `iti_collect.py` 数实际命中信源数 | ≥7 个信源命中 |
| 6 | Gate 拦截次数 | 1-3 | 0 | **真跑** | 完整 ship 中观察 PreToolUse hook `gate.py` 是否对合法 ship 误拦(exit 2) | 0 次误拦(对最终稿 exit 0 放行) |
| 7 | Lint 修复轮数 | 6/3/6 | ≤2 | **真跑** | Stage 3 `fengyun_lint.py` 跑到 0 violation 的轮数 | ≤2 轮 |
| 8 | 端到端总耗时 | 45min | ≤25min | ~~真跑~~ **advisory** | ⚠️ 降级:`feedback_no_time_estimates` 铁律,**不作硬门**;真跑顺手记一笔仅供参考 | 不卡 go/no-go |
| + | verify_baseline 回归 | — | 零回归 | **真跑(免费无副作用)** | `python -X utf8 scripts/verify_baseline.py` | **193 passed / 0 deselected** |

**静态可现在判定(无副作用)**:#1 #2 #3(spec层) #4 #5(W8 实测) → verify 静态轨先测。
**真跑 e2e 才知道**:#5(真跑计数) #6 #7,+ 回归 #+(免费先跑)。

---

## 3. e2e 跑法(从零到一全流程,F1 拍板)

### 3.1 /ship 链路(explorer 实测)

```
/ship <主题>
├─ Stage 1 Collect — subagent fengyun-iti(sonnet)
│    iti_collect.py(I-1 广搜,真读 TrendRadar DB)→ topic_recommender.py(T 排序)
│    → WebSearch ×4-6 → iti_explore.py(I-2 深搜 + aihot ?q=)→ 200字试稿 dogfood
│    产:output/research/<date>-<slug>.md + output/runs/<slug>/iti.invocation.json
├─ Stage 2 Write — subagent fengyun-writer(opus)
│    Skill fengyun-writer 正文 → title_signal.py(≤3 retry)→ ending_signal.py(≤3 retry)
│    产:output/drafts/<date>-<slug>-v0.md + writer.invocation.json
├─ Stage 3 Verify — 主线程 lint + 王小波,然后【同一消息并行】:
│    subagent fengyun-critic-huashu(sonnet)→ huashu-perspective Track B → critic_b_huashu.invocation.json
│    subagent fengyun-critic-content-judge(sonnet)→ content-judge Track C → critic_c_content_judge.invocation.json
│    主线程:critic_vote.py 决议 → verify.invocation.json
│    ship/force_ship → Stage 4;revise → 回 Stage 2(最终稿 4 件 invocation 必须重写)
└─ Stage 4 Publish — subagent fengyun-cover(sonnet)
     huashu-image-curator Mode3 封面 prompt → seedream_client.py(×3 retry,placeholder fallback)
     → illustrate_decider.py 内文图 → cover.invocation.json
     主线程:post_fengyun_publish.py(← PreToolUse hook gate.py 卡 6 件 invocation)
     → 推草稿到「研究Agent的云」草稿箱 → render.invocation.json + Step 9 报告
```

### 3.2 凭证 / 外部依赖(全在风云本机,sandbox 跑不了)

| 依赖 | 配置 | 状态 |
|---|---|---|
| TrendRadar DB | `D:\Dev\TrendRadar\output\rss\2026-05-27.db`(只读) | ✅ 1.27MB 今日已更新 |
| aihot `?q=` | `https://aihot.virxact.com/api/public/items?q=`(公开,需浏览器 UA) | ✅ W8 实测 23 条 |
| Seedream 封面 | `.env` `VOLCENGINE_IMAGE_KEY`(`tools/seedream_client.py` L56) | ✅ key 在 .env |
| 微信草稿箱 | `.env` `WECHAT_APPID` + `WECHAT_SECRET`(`post_fengyun_publish.py` L364) | ✅ key 在 .env;AppID `wx3b564039c7a4560e` |
| we-mp-rss(可选信源) | Docker `localhost:8001` admin/admin123 | 真跑时若容器没起则该信源跳过(有 fallback) |

### 3.3 sandbox 双轨(§8.5.2)

verify 子 agent 在 sandbox 跑不了真凭证步骤(HTTP 000 / 无 .env / 无本地FS)→ **e2e 真跑 + verify_baseline + §8 真跑指标一律主线程动态轨兜底**;verify 子 agent 只跑静态轨(行数 / grep / 文件存在 / 链路文件一致)。commit message 必须诚实标注 `(sandbox fallback - 主线程兜底跑真凭证步骤)`。

### 3.4 真跑副作用(F1 已拍板接受)

- 花 Seedream 图额度(1 封面 + ≤5 内文图)+ 微信 API 额度
- 产 1 篇真草稿推到「研究Agent的云」草稿箱(风云草稿箱手动决定发不发,**pipeline 不自动发布**)
- 产 `output/runs/<slug>/` 6 个 invocation JSON + draft + 图;`output/` 运行时产物不计入 arch-refactor-v1 源码 diff
- ⚠️ **推草稿前主线程明确播报**「即将真推草稿到草稿箱」,但**不再 re-ask**(F1 = 全流程已durable授权)

---

## 4. A/B 对比协议(F2 拍板:用草稿箱已有老稿)

- **新稿** = W10 e2e 真跑产物(新流程,arch-refactor-v1)
- **老稿** = 草稿箱已有 v3/v4(Round 17-25 老流程产物,05-21 anthropic-mythos)
- **比什么维度**(agent 客观列差异,**不打分不判优劣**):
  1. voice 母语化(全角标点 / 翻译腔 / 英式中文)
  2. Vision 选题胆量(从 0 到 1 vs 嚼别人嚼过的)
  3. 排版(huashu 模板落地度)
  4. 封面(花叔自著 metaphor vs 老模板)
  5. 文章结构(开头/结尾 harness 效果)
  6. lint 干净度(破折号/否定排比/AI 味词)
- **⚠️ 最终 A/B 通没通过 = 风云本人 founder verdict(主观),agent 绝不自动下结论**;agent 只交「两稿并排 + 客观差异清单」给风云。

---

## 5. go/no-go 判据 + 主支替换流程 + rollback

### 5.1 go 判据(全满足才算「可替换主支」)

1. §8 静态项全 PASS(#1 #2 #3spec #4 #5静态)
2. verify_baseline **193 passed / 0 deselected** 零回归
3. e2e 真跑子集:#6 gate 0 拦截 + #7 lint ≤2 轮 + #5 真跑信源 ≥7
4. reviewer(全新 session)判「e2e 产出质量达标 + 整个 arch-refactor-v1 达可替换主支标准」
5. Musk 判「过程合规 + 真达成 §8 重构目标 + Idiot Index 合理」
6. **风云 A/B 拍板通过**(founder verdict)

### 5.2 主支替换流程 ⛔(等风云显式说「替换主支」才执行)

```bash
# 前置:三审全过 + 风云 A/B 拍板通过 + 风云显式说「替换主支」
# 旧 main = ae3cb4c 已有 tag backup-pre-refactor-20260526 兜底
git -C D:/Dev/ai-wechat-pipeline branch -M arch-refactor-v1 main
# git branch -M(force rename)把 arch-refactor-v1 重命名为 main,覆盖旧 main 指针
git -C D:/Dev/ai-wechat-pipeline branch --show-current   # 确认 = main
git -C D:/Dev/ai-wechat-pipeline log --oneline -3         # 确认 HEAD = W10 收尾 commit
```

⛔ **绝不自动跑**:任何 agent / 主线程在风云显式说出「替换主支」四个字之前,branch 不动主支。

### 5.3 rollback

```bash
# 替换出问题,回到重构前主支:
git -C D:/Dev/ai-wechat-pipeline checkout backup-pre-refactor-20260526
# 或重建 main 指针到旧 commit:
git -C D:/Dev/ai-wechat-pipeline branch -f main ae3cb4c
# user-level skill 回退(若需要):
cp -r vendor/skills/fengyun-publish/* ~/.claude/skills/fengyun-publish/   # ⚠️ vendor 是新版,回旧版需从 backup tag checkout vendor 再 cp
```

### 5.4 诚实披露(替换前风云必须知道)

- 替换主支主要影响 **git 跟踪的** `tools/` / `.claude/` / `vendor/` / `docs/`。
- **user-level `~/.claude/skills/fengyun-publish/` 已是 199 行新版**(不随 git 分支变)→ 重构对真实 ship 的 skill 行为**其实已经 live**,替换主支只是让 git 主线追平既成事实。
- content-judge / fengyun-writer 等其它 user-level skill 无 vendor 镜像(§8.6 scope 仅 fengyun-publish + huashu-image-curator),其 doc-sync 编辑不进 git;rollback 安全缺口预存于 W9 之前(W9 §4.9 已诚实披露),W10 不扩 vendor scope。

---

## 6. 验收命令(本 wave 专有)

```bash
# 回归基线(免费,主线程动态轨)
python -X utf8 scripts/verify_baseline.py            # 期望 193 passed / 0 deselected

# §8 静态指标
wc -l ~/.claude/skills/fengyun-publish/SKILL.md       # #1 期望 ≤300(现 199)
wc -l vendor/skills/fengyun-publish/SKILL.md          # 镜像核对
grep -rn 'python -c' ~/.claude/skills/fengyun-publish/ vendor/skills/fengyun-publish/ WRITE_AGENT.md   # #2 期望 0
grep -rn '```python' ~/.claude/skills/fengyun-publish/ vendor/skills/fengyun-publish/ WRITE_AGENT.md   # #2 期望 0

# §8 真跑(主线程驱动 /ship,产真草稿)
# Stage 1-4 全流程,过程中记:gate 拦截次数(#6)/ lint 轮数(#7)/ 信源命中数(#5)

# go/no-go 前最后核对 diff 面
git log --oneline backup-pre-refactor-20260526..arch-refactor-v1   # 68 commits
git diff --stat backup-pre-refactor-20260526 arch-refactor-v1      # 86 files
```

---

## 7. 风险 + 兜底(本 wave 专有)

| 风险 | 兜底 |
|---|---|
| e2e 真跑中途某 stage 崩(API 限流 / 凭证过期 / DB 锁) | 诚实记录崩在哪一步;能跑的子集照常验,崩的部分标注「主线程兜底重跑」or「延风云本机」,**绝不假装跑过**(§8.5.2 诚实义务) |
| Seedream 出图失败 | seedream_client 有 placeholder fallback(W7 内藏 retry×3 指数退避);仍失败则记录,不阻断验收(图质量是 ship-time gate 非架构 gate) |
| we-mp-rss 容器没起 | 该信源跳过,有 fallback;信源数仍应 ≥7(TrendRadar DB 5/feed + aihot + WebSearch 已够) |
| gate.py 误拦合法 ship | 这正是 #6 要测的 —— 若真误拦则是 P0 bug,当轮诊断修(§2.1 闭环),不盲推(§8 #12) |
| **整体替换主支误操作** | ⛔ **等风云显式说「替换主支」才跑**;旧 main=ae3cb4c + tag backup 双保险;§5.3 rollback |
| 主线程跑 e2e 时多窗口并发写 | §11 单写者铁律:确认无其它窗口在写 arch-refactor-v1;e2e 只写 output/ 运行时产物不碰源码 |

---

## 8. 三 subagent prompt(全新 session)

### 8.1 verify subagent(静态轨;真跑动态轨主线程兜底)

> 你是 arch-refactor-v1 W10 验收的 verify subagent(只读 + Bash)。工作目录 `D:\Dev\ai-wechat-pipeline\`。跑:① `python -X utf8 scripts/verify_baseline.py` 期望 193 passed / 0 deselected;② §8 静态指标(SKILL.md 行数 ≤300 / Python 伪代码 grep =0 / cover 无模板代码 / ship.md B‖C 并行 dispatch);③ 报每项实测值 + PASS/FAIL。sandbox 拒 Bash → 报「Bash denied」,主线程兜底跑动态轨。**只报结果不改代码。**

### 8.2 reviewer subagent(全新 session,Read/Grep/Glob,无 Write)

> 你是 arch-refactor-v1 W10 验收的 reviewer,全新 session 不知道主线程怎么跑的。审:① W10 e2e 真跑产出(output/runs/<slug>/ 6 件 invocation + draft + cover)质量是否达 ship 标准;② 整个 arch-refactor-v1(对标 ARCH §8 验收表 8 项 + 5 条 invariant)是否达到「可替换主支」标准;③ 有无 P0 阻断。输出 binary verdict:**达标可替换主支 / 未达标(列 P0)**。

### 8.3 Musk 监督员(全新 session)

> 你是 arch-refactor-v1 W10 收尾的 Musk 全程监督员。核验:Q1 W10 执行 vs 规划 Idiot Index;Q2 踩坑诚实度(没跑的有没有诚实标注 §8.5.2);Q3 §8 重构目标是否真达成(不是装饰);Q4 invariant #4 遵守;Q5 三 subagent 真用。binary:**合规(可收尾)/ 偏离(先纠正)**。**特别核验:有没有任何 agent 在风云未显式授权下碰主支替换。**

---

## 9. W10 完工记录(收尾时回填)

> (verify / reviewer / Musk 三审全过 + 风云 A/B 拍板后回填到此 + REFACTOR_PLAN §4.10)
