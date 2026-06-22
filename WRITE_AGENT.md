# WRITE_AGENT.md · 风云 AI 公众号 ship pipeline 系统级宪法

**文档定位**:这是整个 ship pipeline 的**最高执行标准**,优先级高于任何 SKILL.md 描述。
**适用范围**:风云 AI 公众号「研究 Agent 的云」每一篇 ship。
**强制执行机制**:`tools/gate.py`(PreToolUse hook)+ `post_fengyun_publish.py` preflight assertion 双保险。
**版本**:v1.9 · 2026-05-27(arch-refactor-v1 W7 — cover 无模板重做;详见下方 v1.9)
**写作前必读**:本文档,不读不允许动手 — 主线程 Claude 包括本人。

---

## 版本变更日志(读完才往下看)

### v2.0(2026-06-10 — 砍 ending harness + title harness 降档 advisory)

**依据 = W9-after 审计实证**(`reports/dim_trigger_rate_audit_w9_after.json`,321 篇含卡兹克/宝玉/赛博禅心头部真品),不是拍脑袋:

- **Step 3.5 ending harness 整套删除**:4 个维度里「末段字数 ≥150」99.3% 全过(永不触发)、「金句/摘要/召回密度 ≥6」三维把 **92-95% 头部真品判不合格**(全员触发)——1 维永不响 + 3 维全员响 = 零判别力,这套阈值把模仿对象全体判死刑。原 PHASE1 4 信号(b_last_para_chars ρ=+0.300 等)是 critic 特征层的相关性证据,**不构成这套手写阈值的有效性证据**。结尾质量防线由 Step 5 王小波语感预审 + Step 6 花叔 Track B 承担(「愿你也能+颜文字」式公式收尾本就是花叔 emotion 维度的毙稿点,有 verdict 实例:`output/verdicts/guizang-xhs-skill_huashu.json`)。
- **Step 3.3 标题 harness 降档 ADVISORY**:W9 调参后头部真品 verdict pass 率仍仅 **32.7%**(把 67% 模仿对象判死);真实发文 n=13 不足以校准阈值。降为:**跑一次出参考信号,fail 时给 writer 一次自主改标题机会,不循环不阻断**。等数据飞轮攒够真实打开率样本再校准回 BLOCKING。
- `ending_signal.py` / `ending_dedup.py` / `title_signal.py` / `title_dedup.py` **保留在 tools/ 当审计仪器**(`dim_trigger_rate_audit.py` 依赖)——仪器不是引擎,流程不再依赖其 verdict。
- 19 Step → 18 Step;每篇 ship 最多省 6 轮「评分→重写」循环。

### v1.9(2026-05-27 arch-refactor-v1 W7 — cover 无模板重做)

- **物理目的**:把封面从「7 固定模板 + 关键词路由 + 写死英文 prompt + 7 天 dedup」换成「**花叔 cover mode 读文章自著中文 Seedream prompt**(无模板;Style Block 锁品牌色 + 手绘风,主体 metaphor 放给 AI)→ 薄客户端 `seedream_client.py` 出图(retry ×3 指数退避 + placeholder fallback 全内藏)」。
- **物理删(不归档)**:`tools/generate_cover_by_template.py`(名字=by_template,无模板后作废)+ `tools/cover_dedup.py`(无模板就无「撞型」概念)整删;**无 test 引用**。
- **新建**:`tools/seedream_client.py`(薄客户端,ARK 调用迁自旧文件但 prompt **透传**不再 TEMPLATES replace)+ `tools/test_seedream_client.py`(test-first:截断 / placeholder / retry / 透传)。
- **huashu-image-curator 新增 Mode 3 cover**:花叔读文章自著**中文**封面 prompt,输出 JSON `{prompt(中文), aspect, style_anchor(英文,供内文图复用,无签名), metaphor_note}`。责任方仍是 `fengyun-cover` subagent。
- **去云签名**(缩略图零识别)+ **删 5 层英文加固**;**留品牌色** `#F8F0E0` 暖米 + `#D97757` 陶土橙(唯一彩) + 手绘 sketchnote 风。prompt 改**中文**(Seedream 中文原生优化);标题走**模型内渲染**(轻量中文指令)。
- **回写**:本宪法 Step 7-cover / Step 7.2 style_anchor 基底 / Step 总览 / Round 21 决策 2 + `.claude/agents/fengyun-cover.md` + fengyun-publish `SKILL.md` + `references/stage_04_publish.md` + `COVER_STYLE_GUIDE.md`(slim 重写成权威 Style Block)+ `vendor/` 双镜像(fengyun-publish + 新增 huashu-image-curator)。
- 详见 `refactor_specs/wave_07_cover_redesign.md` + `REFACTOR_PLAN.md` §11。

### v1.8(2026-05-27 arch-refactor-v1 W6 — W5 内联 python 过渡命令 → 真 tools CLI)

- **物理目的**:兑现 v1.7 的 W6 follow-up。给 ~9 个无 argparse 工具补真 CLI(test-first),把本宪法 + SKILL/references 里 W5 留作过渡的内联 python 单行命令全部回写成干净 `python tools/X.py --flag`。
- **补 CLI(每工具 test-first,只加 argparse + 读文件 + 打印 JSON,0 改打分/去重/rank 逻辑,反 p-hacking)**:topic_recommender(`--pool/--ws/--out`)、event_dedup(`--in/--days/--include-published/--current-draft/--out`)、title_signal(`--title/--topic-keywords/--body-chars/--draft`)、title_dedup(`--title/--hook-type/--draft/--max-age-days/--max-n-check`)、ending_signal(`--draft`)、ending_dedup(`--draft/--max-age-days/--max-n-check`)、opening_signal(`--trial/--draft`)、opening_dedup(`--trial/--draft/--current-draft`)、illustrate_decider(`--draft --generate --decision --slug`)、iti_explore(`--merge-ws/--out`)。
- **回写**:本宪法 Step 1.x / 3.3 / 3.5 / 7.3 + `SKILL.md` + `references/stage_01/02/04` + `vendor/` 镜像;全文内联 python 过渡命令残留归零。
- **ship.py 编排**:W6 不建 Python ship.py —— W3 `/ship` slash + 5 subagent 已是 orchestrator-worker(invariant #2 统一语言);headless SDK ship.py 0 消费者(cloud 暂停)延 cloud 阶段(invariant #4)。
- 详见 `refactor_specs/wave_06_real_clis.md` + `REFACTOR_PLAN.md` §4.6。

### v1.7(2026-05-27 arch-refactor-v1 W5 — Python 伪代码 → bash 真命令 + DEFAULT-on opt-out)

- **物理目的**:官方 issue #19308 —— Claude 把 Python fenced 伪代码块当 "reference 不是 command"。本宪法 9 处伪代码块全清扫成**可直接运行**形态。
- **三类改造**:① 真 CLI 工具(iti_collect/iti_explore/fengyun_lint/critic_vote/illustrate_decider --dry-run/post)→ 真命令 ② **无 argparse 的 importable-only 函数**(rank_aihot_candidates/score_title/score_ending_signal/check_*_overlap/merge_with_websearch/generate_from_decision)→ 内联 python 单行(读文件;**W6 已全部补真 CLI 替换**)③ skill-invoke(fengyun-writer 改标题/改末段、huashu/content-judge vote)→ 显式「invoke skill」步骤。
- **DEFAULT-on opt-out**:Step 1.x / 选题类条件触发改「默认必跑 + 显式 opt-out」(主条款在 `references/stage_01_collect.md`)。
- **同步**:fengyun-publish `SKILL.md` 修 5 条 W1 遗留假命令(`--pool`/`--draft`/`--entities`/`--generate`,4 工具实际无 argparse)+ `references/stage_01/02/04` 同改 + `vendor/` 镜像。
- **W6 follow-up(已完成,见上方 v1.8)**:给 topic_recommender/title_signal/ending_signal/illustrate_decider 加真 `--draft`/`--pool`/`--generate` CLI(带测试)后,文档内联 python 单行已简化为 `python tools/X.py --draft Y`。
- 详见 `refactor_specs/wave_05_bash_default_on.md` + `REFACTOR_PLAN.md` §4.5。

### v1.6(2026-05-27 arch-refactor-v1 W4 — frontmatter 防伪字段 → invocation log)

- **invariant #3 落地**:frontmatter 回归「文章 metadata + 物理产物指针」(title/digest/author/slug/date/north_star/cover_path/image_paths/image_at_h2_indices)。
- **~25 个 pipeline-state 防伪字段迁走**:所有 `*_pass`/`*_real_run`/`*_source` → `output/runs/<slug>/<stage>.invocation.json`(6 件 pre-publish + render)。
- **gate.py 改写为 invocation log 消费者**:查 6 件齐全 + schema(`assets/run_log.schema.json`)+ `finished_at`<1h + 最终稿 stage 的 `input_hash == sha256(当前 draft)` + `verify.result`∈{ship,force_ship}。
- **反 fake 升级(Newton)**:旧 frontmatter pass_flag 证明不了「评的是最终稿」,`input_hash` 匹配能 —— 不许拿旧版 verdict ship 新稿。
- **scope(spec §1.1):`image_paths`/`cover_path`/`image_at_h2_indices` 留 frontmatter**(物理产物指针 = 真 invariant,非 fake-pass 猜想;避免级联 render/publish 路径)。
- **新增**:`tools/invocation_log.py`(生产+校验)、`tools/validate_run_log.py`(PostToolUse hook)、`tools/ship_complete_check.py`(Stop hook)、`.claude/settings.json` 补齐三层 hook。
- 详见 `refactor_specs/wave_04_invocation_log.md` + `REFACTOR_PLAN.md` §4.4。

### v1.5(2026-05-25 Round 25 — 文内图强制必选 + audit pass)

- **Step 7.2/7.3 强制必选**:任何 ship 必须 `image_paths` 非空 + 每张文件 size ≥ 5 KB
- **0 图 ship 路径删除**:旧 Round 9 `should_illustrate: false` 已废
  - `huashu-image-curator` skill 永远返回 `count ≥ 1`(即使灵魂建议 0 图也强制 1 张 fallback)
  - `illustrate_decider.py` 删 3 个 `return []` 路径
- **Seedream Fallback 链**:retry × 3 指数退避(`time.sleep 1s/2s/4s`)→ daily_quota → `assets/placeholder-sketch.png` × N
- **gate.py 物理硬约束**:`image_paths` 必填非空 + 文件存在 + size ≥ 5 KB
- **`image_generation_degraded=true` 已废**:Seedream 失败走 placeholder,不再 degraded ship
- **audit 修复**(Newton/Musk 二轮 review 后补):
  - Bug B1:`illustrate_decider` docstring 旧示例 `else: image_paths = []` 删
  - Bug B2:`write_metadata` 入口 `assert image_paths` fail-fast
  - Bug B3:3 个 placeholder fallback 路径强制写 `image_at_h2_indices`(防 gate 自阻塞)
  - Bug B4:`fallback_reason` 字段写入 frontmatter(audit trail)
  - G5:retry 真实现 `time.sleep` 指数退避(原 SPEC 描述无代码实现)
  - 字段重命名 `_zero_reason/_round25_placeholder → fallback_reason`(去版本号前缀)
  - placeholder 视觉重做:删「图片生成中」文案 + 删「云」签名 + 删内部 metadata,改抽象 sketch
- **开发监督机制(三人共识)**:spec-first + CI 测试 + 关键节点 diff review,不开会

### v1.5(2026-05-27 W2 arch-refactor — 双轨全自动 + 零人工 gate)

> 用户铁律「注意全流程无人工交互」。W2 wave 把 critic 从三轨砍成双轨,删最后的人工出口。**本条 supersede v1.4 的 auto_partial_pass / auto_abort 描述**。

- **W2.C2 删 humanizer-zh skill**:self-report 无外部验证(11 篇 v0 全 pass 但破折号 9/篇 vs 风云真稿 0.48/篇)。真漏网 2 模式迁 fengyun_lint **R29(破折号 ≤ 3/篇)+ R30(否定排比 ≤ 2/篇)**,阈值用风云本人 56 篇 corpus 实测。
- **W2.C6 删 Track A(score_draft.py)**:质量底线 = lint(机械层,W9 后约 23 条:砍 R2/R4/R13/R14/R16/R21 伪 lint)+ B/C 双轨灵魂共识。
- **双轨对等**:B(huashu)、C(content-judge)任一 reject → revise,删「C 硬否决」特权。
- **隐藏式 3 轮天花板**:`critic_vote.py REVISE_CEILING`(代码层,LLM 不可见)。到天花板仍未双过 → **force_ship**(强制 ship + WARN)。**删 human_gate / partial_pass / auto_abort**。评委 B/C prompt 永不出现「轮次/上限」。
- **R18-P0 也全自动**:末轮 P0 + 未到天花板 → revise 自动删段;到天花板仍 P0 → aborted_r18 自动终止(ERROR 日志,不 ship,无人工)。
- **全流程零人工 gate**:删 Stage 1 选题确认 / 事件去重 confirm / dogfood R18 / lint loop / 封面失败 / 推送失败 等所有 mid-flow 人工出口。唯一人工 = pipeline 外草稿箱审阅 + 点发出。

### v1.4(2026-05-25 Round 24 — 全自动化升级)

> Musk × Jobs × Newton 共识:北极星红线只在草稿箱审阅那一刻。pipeline 内部不再因「等真人确认」停下。
> ⚠️ **W2.C6 superseded**:本节 auto_partial_pass(A≥65)/ auto_abort(A<65)已废 — A 轨删了,改 force_ship。看 v1.5。

- **Step 1.1 删用户确认**:`topic_recommender` 排序后自动选第 1,pass_flag `user_confirmed_topic` → `auto_selected_topic`(无 binary verdict 阻塞)
- **Step 1.5 删 fallback 真人**:dogfood gate confidence < 0.7 → 自动 `degraded: true` + continue,不再 print 等回答
- **Step 6.5.8 自动出口**:原 human_gate 已废,改自动判:
  - 3 轮未过 + A ≥ 65 → `auto_partial_pass: true`(ship)
  - 3 轮未过 + A <  65 → `auto_abort: true`(终止 pipeline)
- **gate.py REQUIRED_PASS_FLAGS** 加 `auto_partial_pass / auto_abort` 作为合法 pass_flag(任一为 true 即满足 critic 类要求)
- **fengyun-self → content-judge 重命名**:Track C critic skill 改名(原 skill 是「风云本人 decision perspective」,Round 24 重新定位为「独立第三方评委」)。引用 `critic_c_source` 描述同步更新

### v1.3(2026-05-25 Round 23 — huashu 高亮 2 bug)
- **Bug 1 punct 错位**:`_fix_cjk_bold_punctuation` 拆分末尾(激进 ASCII 全套)+ 开头(保守只引号/冒号)集合,加 lookbehind 防 `**A**,**B**` 连续 bold 误判
- **Bug 2 高亮过密**:新增 R26(每段 bold ≤ 1)+ R27(全文 ≤ 5,短文 ≤ 3),Musk × Jobs 物理约束(working memory + spotlight)。**用户偏好「比花叔更克制」**:花叔 corpus 抽样 20% 篇单段 ≥ 2 处 / 40% 全文 > 5 处,Round 23 主动选择更严的阈值

### v1.2(2026-05-25 Round 22 收尾)
- **Round 22 P0-6**:gate 防伪扩面到 8 项(原 critic 三轨 + Round 21 humanizer/wangxiaobo + Round 22 新增 writer / huashu_image_curator) — 主线程任何 step「假装跑 skill」都会被当场抓
- **Round 22 #1**:`iti_collect.py` 默认写 `output/candidates/YYYYMMDD.json`,Step 1.x 可读
- **Round 22 #2**:`event_dedup` 扫两个 source(drafts + runs 含 media_id 的存档),解决「已发还推荐」
- **Round 22 #5**:`iti_explore.py` CLI 新增 `--main-source-urls`,Step 2 WebSearch 找的 URL 可显式注入
- **Round 22 #3**:Step -1 / 0 / 0.1 编号歧义澄清 + 允许「TBD 占位 + Step 1.1 后回填」

### v1.1(2026-05-25 Round 21)
- **Round 21 决策 1**:排版统一花叔 — `--render-mode legacy` 砍 + `style=default/classic` 分支砍(78 行 + 13 个 helper)。**huashu 是唯一活跃渲染路径**
- **Round 21 决策 2**:封面 + 内文图风格强制一致 — 出 `<slug>-cover.style_anchor.txt` sidecar,Step 7.2 huashu-image-curator 必须读这个 anchor 作为输入(**W7 superseded**:出 sidecar 的工具从已删的 `generate_cover_by_template.py` 改为 `seedream_client.py` 的 `--style-anchor`;sidecar 机制 + 风格一致约束不变)
- **Round 21 P0-14**:`illustrate_decider` 加 SetLimitExceeded / safe_experience 关键词(火山新错误码)
- **Round 21 P0-16**:`gate.py parse_frontmatter` 支持多行 YAML list(image_paths / image_at_h2_indices)
- **Round 21 P0-9**:gate 防伪加 humanizer / wangxiaobo
- **Round 21 P0-4**:`opening_signal` reframe regex 允许空格 / 逗号
- **Round 21 P0-17**:layout_rules HTML 上限 20000 → 60000(对齐微信真实 65000 物理上限);fengyun_lint 加 R12b html_size_warn

### v1.0(2026-05-25 Round 17 落地)
- 系统宪法首版 + gate.py PreToolUse hook + 19 step 全流程颗粒度

---

## ⛔ 北极星红线(NORTH_STAR)— 永不变

> **最终人工动作只有一个:风云在公众号草稿箱审阅 + 手动发出。**

任何环节的「自动决策 / 自动 ship」不得替代这条。gate 拦的是「半成品推草稿」,不是风云的最终一击。

---

## ⛔ Preflight 红线 — 系统启动前置自检(2026-05-25 v1.0 落地)

> **每次「开始用系统」前必跑 `.\tools\preflight.ps1`,P0 全绿才允许进入任何 Step。**

### 为什么有这条红线

整套链路是 7 个独立服务的**串联**(Docker → we-mp-rss → cookie → TrendRadar → HF Spaces RSSHub → Email-to-RSS Worker → 公网 RSS)。任意一环挂掉 fengyun-publish 都会**静默 degraded**(信源数减少但不 abort),最终推到草稿箱的文章信息不全 / 角度偏。

2026-05-25 实测发现:Docker Desktop 没开 + TrendRadar 3 天没跑 + rsshub.app 公共实例对本机 IP 403 → 这三件事**任何一件单独发生**,文章质量都会肉眼可见地下降,但 pipeline 不会停。所以**必须前置 hard check**,把"系统启动"这一步本身物理化。

### Preflight 7 项检查

| # | 项 | 优先级 | 失败 = 后果 |
|---|---|---|---|
| 1 | Docker Desktop daemon | **P0** | 整套链路死透 |
| 2 | we-mp-rss 容器 (localhost:8001) | **P0** | 16 个公众号 feed 全空 |
| 3 | we-mp-rss cookie 新鲜度(抽 1 feed 看 entry) | **P0** | 即使容器活,cookie 死也拉空 |
| 4 | TrendRadar `latest_daily.md` mtime ≤ 36h | **P0** | iti_collect 跳过这个信源,选题候选池减少 1/6 |
| 5 | 本机 RSSHub 容器(localhost:1200)+ B/知乎 cookie 双测 | **P0** | 7 个 B 站/知乎 feed 503 拉空(2026-05-26 HF Spaces 路径已 deprecated:HF 中国大陆 IP 返回 418) |
| 6 | Email-to-RSS Worker(配置后激活) | P1 | Substack 私有 newsletter 拿不到 |
| 7 | `rsshub.app` 公共实例(已知挂,提醒用) | P1 | 提示自建迁移进度 |

### 强制执行机制

| 层 | 机制 |
|---|---|
| **L1 lint 层(本红线)** | `.\tools\preflight.ps1` 跑出 P0 FAIL → 退出码 1 → 主线程禁止进入 fengyun-publish Step 1 |
| **L2 hook 层** | `tools/gate.py` PreToolUse 在 ship 推草稿前再抽 1 项 P0 复查(防止启动后服务挂掉) |
| **L3 人格层** | 主线程 Claude 必读本红线;任何「我先跳过 preflight 直接开干」的行为视同破坏宪法 |

### 救场命令(常见 P0 失败)

```powershell
# Docker Desktop 没开
# → 系统托盘点 Docker 图标启动 GUI;等鲸鱼变绿(约 10-30 秒)

# we-mp-rss 容器没跑
docker start we-mp-rss
# 或首次部署
docker run -d --name we-mp-rss -p 8001:8001 ghcr.io/rachelos/we-mp-rss:latest

# cookie 过期(约 80 小时一次)
# → 浏览器开 http://localhost:8001 重新扫码

# TrendRadar latest_daily.md 过期
# 推荐入口(已修 Windows GBK 编码 emoji 崩):
.\tools\run_trendradar.ps1
# 或后台跑:
.\tools\run_trendradar.ps1 -Background
```

### 部署完 HF Spaces / Email-to-RSS 后

把 URL 填进 `tools/preflight.ps1` 顶部的 `$HF_RSSHUB_URL` / `$EMAIL_RSS_URL` 两个变量,**P1 项自动从 SKIP 升为实际检查**。

### 关联

- 一键脚本:`tools\preflight.ps1`
- HF Spaces 部署指南:`docs\rsshub_hf_spaces_setup.md`
- Email-to-RSS 部署指南:`docs\email_to_rss_setup.md`
- 信源现状报告:`reports\phase17_*.md` 4 份

---

## ⛔ 商业机密三级红线(R18)— 永不变

P0(致命) → 立即 abort,不进任何兜底:
1. 自暴 AI 生成(「本文由 AI 写 / 作为 AI / Claude 帮我写」)
2. 自暴架构(harness / writer / critic / lint / 三轨 / vote / 飞轮 / pipeline)
3. 自暴 skill 名 / 模型名 / prompt 配方
4. 自暴工具栈(「我的豆包 / 我的 DeepSeek / 我的 Cloudflare Worker」)
5. 自暴自动化(「自动 ship / cron 发布」)

P1 / P2 严重度递降,但任何级别命中都不允许过 gate。

---

## 全流程 18 个 Step 总览(v2.0 砍 ending harness 后 19→18)

> ⚠️ **W4 全局(2026-05-27,arch-refactor-v1)— 读任何 Step 前先看这条**:
> **Step 3 / 3.3 / 3.5 / 4 / 5 / 6 / 6.5.8 / 7.2 / 7-cover 下文里的所有 `*_pass` / `*_real_run` / `*_source`
> (writer/title/ending/lint/wangxiaobo/critic_b/critic_c/critic_vote/force_ship/huashu_decision/huashu_image_curator/cover_pass)
> 不再写 draft frontmatter** —— 改为该 stage 跑完调
> `python tools/invocation_log.py write --slug <slug> --stage <stage> --skill <name> --input-file <file> --output <file> --result <result>`,
> 写 `output/runs/<slug>/<stage>.invocation.json`。gate 查 6 件 pre-publish invocation(见 **Step 8 ②**)。
> 下文各 Step 的 frontmatter pass_flag 示例是 **W4 前历史写法,保留作 PRD 连续性**;**实际以 Step 8 ② + `references/frontmatter_checklist.md` 为准**。
> frontmatter 现只留 metadata + 物理产物指针(title/digest/author/slug/date/north_star/cover_path/image_paths/image_at_h2_indices)。

**编号约定(Round 22 #3 澄清)**:
- **Step -1 / 0 / 0.1 全是「写作前置层」L0** — 不管负号还是 0,**全部都是 ship 开始的第一批动作**,顺序就是文档列出的(L0 → L1 → L2 ...)。负号**不是「在 0 之前才存在」**,而是「比 0 更先于内容(选题前的元意图)」的语义标记。
- 流程实际执行顺序:Step -1(填北极星) → Step 0(读 voice-dna) → Step 0.1(style 路由) → Step 1.0(广搜) → ...
- 隔壁 e2e 实测发现 Step -1 可能要在 Step 1.x 选定主题后才能填(因为不知道主题没法填北极星)。**这种情况允许「占位 + 回填」**:Step -1 先用「TBD」占位通过 gate,选完主题后回 Step -1 真填(runlog 记录回填动作)。

```
Step -1   北极星填空(BLOCKING,允许 TBD 占位 + Step 1.1 后回填)
Step 0    Voice DNA + corpus 必读(BLOCKING)
Step 0.1  Style 路由(Round 21 后 huashu 唯一活跃路径,default/classic 已砍)
─── 选题层(ITI 第一段)───
Step 1.0  ITI I-1 广搜聚合候选(BLOCKING)
Step 1.x  topic_recommender 排序 + event_dedup 去重(BLOCKING)
Step 1.1  选定单一主题 + entities + slug
─── 试稿层 ───
Step 1.5  dogfood gate + opening harness(BLOCKING,上限 3 retry)
─── 调研层(ITI 第二段)───
Step 2    ITI I-2 深搜调研 → research.md(BLOCKING)
─── 写作层 ───
Step 3    fengyun-writer 写完整稿 4000-5000 字(BLOCKING)
Step 3.3  标题信号检查(ADVISORY,跑一次记参考,v2.0 降档不拦路)
          (v2.0 已删 Step 3.5 ending harness — W9 审计证伪判别力)
─── 清洁层 ───
Step 4    fengyun_lint 机械层(BLOCKING;含 W2.C2 新增 R29 破折号 + R30 否定排比)
Step 5    wangxiaobo-perspective 语感预审(BLOCKING)
          (W2.C2:humanizer-zh 已删,真漏网 2 模式迁 fengyun_lint R29/R30)
─── 评审层(W2.C6 双轨全自动)───
Step 6    双轨 critic vote B+C(BLOCKING;删 Track A score_draft)
Step 6.5  critic-revise loop(条件 BLOCKING;隐藏 3 轮天花板,评委不知)
Step 6.5.8 force_ship 自动出口(到天花板仍未双过 → 强制 ship + WARN,无人工)
─── 视觉层 ───
Step 7.1  函数预筛内文图候选位置
Step 7.2  花叔 Mode 2 配图决策(BLOCKING)
Step 7.3  内文图 Seedream 生成 + write_metadata(BLOCKING)
Step 7-cover 封面生成(W7 无模板:花叔 Mode 3 + seedream_client)(BLOCKING)
─── 出版层 ───
Step 8    layout_rules 渲染 + post_fengyun_publish(BLOCKING · gate 守门)
Step 9    报告 + audit log
```

---

## Step -1 · 北极星填空

**触发**:任何 ship 开始的第一动作。

**输入**:用户的主题描述。

**执行**:写下 `读完应该感受到 ____` 一句话填空(≤ 30 字)。

**输出**:`output/runs/<slug>.runlog.jsonl` 第一行 `{"step": -1, "north_star": "..."}`

**BLOCKING**:不填,所有后续 step 全部 abort。

**pass_flag**(frontmatter):`north_star: "..."`

**失败回退**:无 — 必须填。

---

## Step 0 · Voice DNA + corpus 必读

**触发**:Step -1 通过后。

**输入**:`~/.claude/skills/fengyun-writer/references/voice-dna.md` + `~/.claude/skills/fengyun-writer/corpus/growth/*.md`

**执行**:
1. Read voice-dna.md 完整版
2. 随机 Read 3-5 篇 corpus 文章

**输出**:仅上下文加载,无文件产物。

**BLOCKING**:跳过 = 用 Claude 默认语调 = 失败。

**pass_flag**(runlog):`{"step": 0, "voice_dna_loaded": true, "corpus_samples": ["A.md", "B.md", "C.md"]}`

**失败回退**:无。

---

## Step 0.1 · Style 路由

**触发**:Step 0 完成后。

**输入**:用户偏好(默认 huashu)。

**执行**:决定 frontmatter `style:` 字段。
- 不写 → 默认 huashu(花叔暖象牙 + 陶土橙,**当前默认**)
- `style: huashu` + `theme: A|B` 显式
- `style: default` opt-out 回原蓝灰

**输出**:无(暂存待写 frontmatter)。

**pass_flag**:`style_routed: true`(frontmatter 在 Step 3 创建时一并写)

---

## Step 1.0 · ITI I-1 广搜

**触发**:Step 0.1 完成后。

**输入**:用户主题词或「拉今天热点」。

**执行**:
```bash
# Round 22 #1 升级:iti_collect 默认写 output/candidates/YYYYMMDD.json
python tools/iti_collect.py --hours 24
# 可指定 --out 自定义路径,或 --no-write 只 stdout
# 同时主线程必跑 WebSearch 中英文各 1-2 次补位
```

主线程调用 `aihot` skill 拉 24h 精选 + `iti_collect.py` 拉 6 信源(aihot + we-mp-rss + TrendRadar + arxiv + smol.ai + WebSearch)。

**输出**:
- `output/candidates/YYYYMMDD.json`(Round 22 #1 默认路径,Step 1.x topic_recommender 读这个)
- 候选 ≥ 10 条(硬约束),目标 15-25 条(甜蜜点),上限 30 条

JSON schema:`{generated_at, hours_window, n_total, n_unique, degraded, sources_ok, sources_failed, stats_per_source, items: [...]}`

**BLOCKING**:候选 < 10 → 主线程必须再跑 WebSearch 补足。

**pass_flag**(runlog):`{"step": "1.0", "candidates_n": 22, "sources": ["aihot", "we-mp-rss", ...], "candidates_json": "output/candidates/YYYYMMDD.json"}`

**失败回退**:某个信源挂 → 跳过该信源,但总数仍要 ≥ 10。

---

## Step 1.x · topic_recommender 排序 + event_dedup 去重

**触发**:Step 1.0 完成后。

**输入**:候选 JSON。

**执行**:
真 CLI:topic_recommender 排序 → event_dedup 去重(读候选 JSON,输出首个非撞型 chosen):
```bash
python tools/topic_recommender.py --pool output/runs/<slug>/iti_pool.json --out output/runs/<slug>/ranked.json
python tools/event_dedup.py --in output/runs/<slug>/ranked.json --days 7 --include-published --out output/runs/<slug>/chosen.json
```
- chosen.json 的 `chosen` 字段 = 单条候选(filtered top 1);`filtered` = 全部非撞型候选
- **Bug 4**(Round 17):Step 1.x 还没写 draft,不传 `--current-draft`;**Round 22 #2**:`--include-published` 默认 on,扫 drafts/ + runs/*.json 有 media_id 的存档

**输出**:`chosen_candidate` 单条 dict + entities 提取。

**BLOCKING**:event_dedup 7 天内撞型 → 弃用该候选,选下一个。

**Round 22 #2 升级**:event_dedup 现在扫两个 source —
1. `output/drafts/*.md` 最近 days 天 mtime 的草稿
2. `output/runs/*.json` 含 media_id 字段的已发布存档(避免「TrapDoor 已发还推荐」)

**pass_flag**(runlog):`{"step": "1.x", "chosen_title": "...", "event_dedup_pass": true}`

**Round 17 验证结果**(2026-05-25):此前怀疑的「score 全 0」**误诊** — cli_demo 实测候选评分正常分布 0.08-1.00,aihot 字段名 `title`/`summary` 跟 `rank_aihot_candidates` 取值一致,逻辑无 bug。继续正常使用。

---

## Step 1.1 · 自动选题 + slug + entities

**触发**:Step 1.x 完成后。

**输入**:chosen_candidate(`topic_recommender` 排序 + `event_dedup` 过滤后的 top 1)。

**执行**(Round 24:全自动,不等用户):
1. 主线程提取 slug(`yyyymmdd-<key-words>` 格式)
2. 提取 entities(2-5 个核心关键词)
3. **直接采用 ranked top 1**(`topic_recommender` 已给出客观排序;`event_dedup` 已过滤 7 天撞型)
   - 用户介入只在最终草稿箱审阅那一刻(NORTH_STAR 红线)— pipeline 内部不再等 binary verdict

**输出**:`output/runs/<slug>.runlog.jsonl` 写 `{"step": "1.1", "slug": "...", "entities": [...], "auto_selected": true, "selection_rank": 1}`

**BLOCKING**:`event_dedup` 全 7 天撞型(连备选都撞)→ 报警 + auto_abort;非用户确认问题。

**pass_flag**:`auto_selected_topic: true`(取代原 `user_confirmed_topic`)

---

## Step 1.5 · dogfood gate + opening harness

**触发**:Step 1.1 完成后。

**输入**:slug + entities + north_star。

**执行**:
1. 调 `fengyun-writer` skill 出 200 字试稿开头(只开头,不完整稿)
2. 跑 `score_opening_signal()`(W9 后:物理约束 + 公式新鲜度 R28 唯一评分维;砍 反差/具体/信息维,拆情绪锚点留第一人称密度)
3. 跑 `check_opening_overlap()` 30 天回看 dedup
4. **content-judge skill** binary verdict「这是不是风云会写的开头」(原 fengyun-self,Round 24 改名为独立第三方评委)
5. 任一 fail → revise → 上限 3 retry

**评分阈值**:
- 物理约束:真首段 ≥ 25 字(W9: 50→25,B4 median 26;修字段名歧义=真·首段)+ 第一人称密度 ≥ 5/千字
- 公式新鲜度 ≥ 6/10(W9 后唯一保留评分维,fy 58.1% 健康)
- dedup:token Jaccard ≤ 0.30 + 5-gram ≤ 0.20

**输出**:`output/runs/<slug>_opening_v{1-3}.md`(每轮试稿)+ 最终 200 字试稿。

**BLOCKING**:3 轮都 fail → 走 partial_pass(用最后一版,记 degraded)。

**pass_flag**(frontmatter):`dogfood_pass: true`(content-judge 挂名意愿 = yes 才算 pass)

**Round 24 自动出口(取代旧 fallback 真人)**:
- content-judge 输出 confidence < 0.7 → frontmatter 写 `dogfood_pass: true` + `dogfood_degraded: true` + `dogfood_degraded_reason: "content-judge confidence=<x> < 0.7"`,**自动继续**不等用户回答
- content-judge skill 不存在 → 同样自动 degraded continue(`dogfood_degraded_reason: "content-judge skill missing"`)
- pipeline 内部任何 confidence 不足的判断都走 degraded continue,不阻塞 ship。最终人工动作只在草稿箱审阅那一刻(NORTH_STAR 红线)。

---

## Step 2 · ITI I-2 深搜调研

**触发**:Step 1.5 dogfood 通过。

**输入**:slug + entities + chosen_candidate。

**执行**(**严禁主线程偷懒手工组装**,必须真调):
**W8 E1:I-2 不再镜像 I-1 的 4 个 generic query**。深搜三路 = WebFetch T 选定主源 url(`chosen.json` 的 `chosen.url` → `--main-source-urls`)+ aihot `?q=` 实体搜索(已内置 explore_topic 的 `aihot-query` 源)+ **1 个 topic-specific 补充 WebSearch**(只补 Python 脚本拉不到的角度)。`explore_topic` 用下方真 CLI;`result["facts"]` = 本地 + API 事实(we-mp-rss / trendradar / aihot-query / corpus grep / arxiv / topic_hotness / safe_webfetch)。要跟 WebSearch 池合并落 facts.json 用 `--merge-ws`(见下方 CLI 用法 + `references/stage_01_collect.md` Step 2)。

**CLI 用法(Round 22 #5 升级,新增 --main-source-urls)**:
```bash
python tools/iti_explore.py <slug> <title> \
    --entities Anthropic Karpathy pre-training \
    --main-source-urls https://example.com/a https://example.com/b \
    --merge-ws output/runs/<slug>/ws_items_i2.json \
    --out output/runs/<slug>/facts.json
```

**输出**:`output/research/<slug>.md`,含:
- 北极星(从 Step -1)
- 核心事件 3 句话摘要
- **5-10 条带 URL 的事实清单**(不是 manual 凑数)
- 3-5 条「我的角度可以是 ___」候选

**BLOCKING**:facts 少于 5 条 → 必须再跑 WebSearch / WebFetch 补足。

**pass_flag**(runlog):`{"step": 2, "research_facts_n": 12, "research_path": "output/research/<slug>.md", "websearch_count": 1}`(W8 E1:I-2 = 1 个补充 query,不再 4 次)

**失败回退**:某个 API 挂 → safe_webfetch UA 轮换 + retry × 2。

---

## Step 3 · fengyun-writer 写完整稿

**触发**:Step 2 完成 + research.md 存在 + facts ≥ 5。

**输入**:research.md + north_star + style 路由。

**执行**:invoke `fengyun-writer` skill 完整写作模式。

**输出**:`output/drafts/<slug>-v0.md`,字数 4000-5000(硬约束)。

frontmatter 必带:
```yaml
title: "..."
digest: "..."
author: "研究Agent的云"
slug: "..."
date: "yyyy-mm-dd"
style: huashu  # 或不写默认 huashu
north_star: "..."  # 从 Step -1
```

**BLOCKING**:
- 字数 < 4000 或 > 5000 → revise
- R18 P0 命中 → abort
- 5-6 个 H2 章节缺失 → revise
- 金句标注 < 3 处 → revise(R28 强制):writer 必须在写作时用 `**...**` 标注 3-5 处核心金句(读者可以「带走」的句子:核心洞察 / 情感锚点 / 收尾金句)。**不是事后手动补,是 writer 在 Step 3 写作时就标好**。lint R28 会在 Step 4 检查,低于 3 处直接阻断

**pass_flag**(frontmatter):
- `writer_pass: true` + `writer_word_count: 4200`
- **Round 22 P0-6 防伪扩展**(必填,gate 强制):
  - `writer_real_run: true` — **必须真 invoke fengyun-writer skill**,不许主线程拍脑袋写
  - `writer_source: "fengyun-writer skill 3 retry round=1"` — 真实出处描述(版本/round/时间戳)
- gate 看到 `writer_pass: true` 但缺 `writer_real_run / writer_source` → fake-pass 防伪触发 → 阻断 ship

**失败回退**:fengyun-writer skill 不存在 → 降级到 khazix-writer(且后续 critic 切单轨)。

---

## Step 3.3 · 标题信号检查(v2.0 降档 ADVISORY,2026-06-10)

**触发**:Step 3 完成。

**输入**:draft frontmatter title + topic entities + body word count。

**执行**(**跑一次,不循环,不阻断**):
① 真 CLI:title_signal 评分(给 hook_type)→ title_dedup 去重(`--draft` 防 self-match,Bug 4):
```bash
python tools/title_signal.py --title "<TITLE>" --topic-keywords <e1> <e2> --body-chars <N>
python tools/title_dedup.py --title "<TITLE>" --hook-type <H> --draft output/drafts/<slug>-v0.md --max-age-days 14 --max-n-check 10
```
② 两个 JSON 输出**原样记入 run log 作参考信号**(数据飞轮校准材料)。
③ signal `verdict==fail` 或 dedup 撞型 → 把 `redo_feedback` 给 `fengyun-writer`(改标题模式,**只改 frontmatter title**)**一次**,由 writer 自主裁量改或不改;改完**不回评**,直接进 Step 4。

**为什么 ADVISORY 不 BLOCKING**(v2.0):W9 调参后头部真品(321 篇审计)verdict pass 率仍仅 32.7%——闸门把 67% 模仿对象判死 = 阈值体系无判别力;真实发文 n=13 不足以校准。**dedup 撞型信号仍最有参考价值**(防 14 天内连续同型标题),所以保留传给 writer。等数据飞轮攒够真实打开率样本,再校准回 BLOCKING(校准动作必须有独立科学动机,反 p-hacking)。

**产物**:无独立 invocation;title_signal/title_dedup 的 JSON 进 writer.invocation.json 的 summary 或 run log 即可。

---

## Step 3.5 · (v2.0 已删:ending harness,2026-06-10)

**砍除依据**(W9-after 审计 `reports/dim_trigger_rate_audit_w9_after.json`,321 篇含头部真品):
- 「末段字数 ≥150」hit 99.3% — **永不触发的死维度**
- 「金句/摘要/召回密度 ≥6」三维 trigger 91.9% / 94.8% / 93.2% — **把 92-95% 头部真品判不合格**
- 1 维永不响 + 3 维全员响 = 零判别力;这套阈值把模仿对象全体判死刑

**结尾质量防线移交**:Step 5 王小波语感预审 + Step 6 花叔 Track B(公式化收尾/「愿你也能+颜文字」本就是花叔 emotion 维度毙稿点,实例见 `output/verdicts/guizang-xhs-skill_huashu.json`)。

`ending_signal.py` / `ending_dedup.py` 保留在 tools/ 当审计仪器(`dim_trigger_rate_audit.py` 依赖),ship 流程不再调用。

---

## Step 4 · fengyun_lint 机械层

**触发**:Step 3.5 完成。

**输入**:draft path。

**执行**:
fengyun_lint 真 CLI(单 positional path):
```bash
python tools/fengyun_lint.py output/drafts/<slug>-v0.md
```
- 跑机械层 lint(**W9 砍 R2/R4/R13/R14/R16/R21 伪 lint + 修 R7 词典**,留约 23 条机械核 + huashu 块),打印 violations + 写 `<draft>.lint.json` sidecar;high severity > 0 → revise(连改 3 轮还 high → 走 6.5 partial_pass + degraded)

**已知 bug**(Round 17-23 全修):
- R0 半角标点误报技术标识符 `.env / .md / .cursorrules`
- ~~R8 / R13 关于「替代」自相矛盾(Round 19 P0-5 修)~~ **R13 已于 W9 砍**(无源 craft,content-judge M6 接管焦虑铺垫判断)
- R12 vs HTML 上限 20000 结构性冲突(Round 21 P0-17 修:HTML 上限抬到 60000)
- **Bug 1 标点错位(Round 23 修,2026-05-25)**:`**xxx**` 高亮框前的 ASCII 引号 / 半角冒号被吸进框。修法:`_fix_cjk_bold_punctuation` 用拆分集合 — 末尾踢出激进(全套 ASCII + 全角),开头踢出保守(只全角 + ASCII 引号 + 冒号,避免 `**A**,**B**` 连续 bold 误判)
- **Bug 2 高亮过密(Round 23 修,2026-05-25)**:新增 R26 + R27 双密度规则。Musk × Jobs 共识硬约束:每段 bold ≤ 1 处 + 全文 ≤ 5 处(短文 < 1000 字按比例缩放到 ≤ 3)

**Round 21 P0-17 新增 R12b**:`html_size_warn` — markdown × 5 倍膨胀估算超 50000 → low severity warn(不阻断,但提示离 60000 硬上限近)

**Round 23 新增 R26 / R27**:
- `R26_huashu_bold_per_para`(medium):每段 bold ≥ 2 处 → 阻断 ship。物理依据:单段注意力 spotlight 1 chunk
- `R27_huashu_bold_total`(medium):全文 bold > 5 处(短文 > 3 处)→ 阻断 ship。物理依据:working memory 4±1 chunk 上限
- ~~跟 R21_bold_ai_padding 互补~~ **base R21(粗体注水 `R21_bold_ai_padding`)已于 W9 砍**(craft,content-judge D-3 typography 接管);R26 看单段 / R27 看全文上限是 huashu 块专属,保留。⚠️ **编号复用**:huashu 规则族另有一条 active 的 `R21_huashu_h2_pattern`(H2 命中 3 模式,style:huashu 专属,未砍)—— 全文「W9 砍 R21」均指 base 粗体注水,非此条

**Round 24 新增 R28(B 类长文粗体下限)**:
- `R28_huashu_bold_minimum`(medium):B 类长文(≥ 3000 总字数)全文 bold < 3 处 → 阻断 ship
- 跟 R27 互补:R27 设上限(防堆砌),R28 设下限(防裸文)
- e2e 实测发现:主线程跳过内文图后连带跳过 bold 意愿。R28 确保长文至少有 3 处核心金句
- Round 25 修:阈值从 3500 CJK 降为 3000 总字数(技术文 CJK 占比低,如 TrapDoor 文 4358 总字但仅 2810 CJK,原阈值漏检)
- 短文(< 3500 字)不触发,R26 段密度兜底即可

**BLOCKING**:high severity > 0 → revise。**partial_pass 允许**:连改 3 轮还 high → 走 6.5 partial_pass + 记 degraded。

**pass_flag**(frontmatter):`lint_pass: true` 或 `lint_partial_pass: true` + `lint_high_count: 0`

---

## Step 4.5 · (W2.C2 已删:humanizer-zh 去 AI 味)

> **W2.C2(2026-05-27)删除**:humanizer-zh skill 是 self-report 无外部验证(11 篇 v0 全
> `humanizer_pass: true` 但破折号实际 9/篇 vs 风云真稿 0.48/篇)。真漏网的 2 个模式迁到
> fengyun_lint **R29(破折号 ≤ 3/篇)+ R30(否定排比 ≤ 2/篇)**,阈值用风云本人 56 篇
> corpus 实测(invariant #4「0 消费者 = 0 生产」)。无独立 Step 4.5,Step 4 lint 直接接 Step 5。

---

## Step 5 · wangxiaobo-perspective 语感预审

**触发**:Step 4 lint 通过(W2.C2 后无 Step 4.5)。

**输入**:draft 全文。

**执行**:invoke `wangxiaobo-perspective` skill。

**输出**:王小波诊断报告(≤ 300 字),含具体翻译腔位置 + 母语替代。

**BLOCKING**:发现翻译腔 → 主线程必须按建议修正,然后 re-invoke 验证 pass。

**pass_flag**(frontmatter):
- `wangxiaobo_pass: true` + `wangxiaobo_revisions: 2`(改了几处)
- **Round 21 P0-9 防伪**(必填,gate 强制):
  - `wangxiaobo_real_run: true` — **必须真 invoke wangxiaobo-perspective skill**
  - `wangxiaobo_source: "wangxiaobo-perspective skill, found N translation-tone hits"` — 真实出处
- gate 看到 `wangxiaobo_pass: true` 但缺 `wangxiaobo_real_run / wangxiaobo_source` → fake-pass 防伪触发 → 阻断 ship

---

## Step 6 · 双轨 critic vote(W2.C6 双轨全自动,2026-05-27)

**触发**:Step 5 通过。

**输入**:draft 全文 + Step 5 pass 状态。

**W2.C6 变更**:删 Track A(score_draft.py 数字分)。质量底线 = lint(机械层,W9 后约 23 条:砍 R2/R4/R13/R14/R16/R21 伪 lint)+ B/C 双轨灵魂共识。双轨**对等**,任一 reject → revise(无「C 硬否决」特权)。

**执行**(**严禁主线程偷懒**,B/C prompt 保持天真严格、绝不提轮次/上限):
1. **Track B**:invoke `huashu-perspective` skill → binary ship/not_ship + 灵魂位置
2. **Track C**:invoke `content-judge` skill → 挂名意愿 yes/no
3. 两轨 verdict(累积各轮)写 `rounds.json`,跑双轨门控树 + 隐藏天花板:
```bash
python tools/critic_vote.py --all-rounds output/runs/<slug>/rounds.json --out output/runs/<slug>/vote.json
```
- 返回 decision:`ship` / `revise` / `force_ship`(隐藏天花板)/ `aborted_r18`;exit code 0=ship / 1=revise / 2=abort / 4=aborted_r18

**R18-P0 全自动**(无人工):末轮 lint 命中 R18-P0 → 跳过 force_ship;未到天花板 → revise 自动删段;到天花板仍 P0 → aborted_r18 自动终止(ERROR 日志,不 ship)。

⚠️ **全流程不中断**:双轨 vote 必须在同一轮消息内连续完成(Track B → C),不许停下来等用户。完成后直接进 critic_vote.py 判定。

**pass_flag**(frontmatter):
- `critic_vote_pass: true`(decision = ship,双轨共识)/ 或 `force_ship: true`(隐藏天花板强制 ship)
- `critic_b_verdict: "ship"` / `critic_c_verdict: "ship"`
- **fake-pass 防伪**(必填,gate 强制 — `critic_vote_pass=true` 时必查):
  - `critic_b_real_run: true` — **必须真 invoke huashu-perspective skill**
  - `critic_b_source: "huashu-perspective skill v1, ship verdict, 灵魂 ✓"` — 真实出处 + binary verdict
  - `critic_c_real_run: true` — **必须真 invoke content-judge skill**
  - `critic_c_source: "content-judge skill, 挂名意愿 yes, ..."` — 真实出处
- gate 任一缺失 → fake-pass 防伪触发 → 阻断 ship(W2.C6 删 critic_a_real_run/critic_a_score)
- **审计实证**(2026-05-25):此防伪当场抓住主线程之前的 fake-pass(verdict 直接拍脑袋写「ship」没真调 skill)

---

## Step 6.5 · critic-revise loop

**触发**:Step 6 verdict = revise。

**输入**:critic 反馈 + draft。

**执行**:
1. 生成 `revise_brief.md`(critic 反馈 → 具体段落改稿指南)
2. invoke fengyun-writer skill「改稿模式」(±10% 字数硬约束,不大改重写)
3. 重跑 Step 4 → 4.5 → 5 → 6
4. 上限 3 轮

**BLOCKING**:
- 改稿循环由 critic_vote.py 隐藏天花板裁决(评委不知有上限,你也不许在改稿时透露)
- 到天花板仍未双过 → 走 Step 6.5.8 force_ship
- 末轮 R18-P0 命中 → 未到天花板 revise 自动删段 / 到天花板 aborted_r18 自动终止

**pass_flag**(frontmatter):`revise_rounds: 0/1/2/3` + `revise_loop_pass: true`

---

## Step 6.5.8 · 隐藏天花板 force_ship(W2.C6 全自动闭环,2026-05-27)

**触发**:Step 6.5 改稿到隐藏天花板(critic_vote.py `REVISE_CEILING`)仍未双过。

**执行**(全自动,不等真人,**天花板数字绝不写进评委 prompt**):
末轮决议由 `critic_vote.py --all-rounds` 代码层裁决:

| 末轮情况 | decision | pass_flag |
|---|---|---|
| 到天花板仍 revise + 末轮**无** R18-P0 | `ship` + force_ship | `force_ship: true`(进 Step 7 封面 + WARN 日志)|
| 末轮**有** R18-P0(到天花板)| `aborted_r18` | 自动终止 + ERROR 日志(不进 Step 7/8,不 ship 自爆稿)|

**实现位置**:`tools/critic_vote.py::_force_ship_result()`(到天花板 force_ship);R18-P0 分支在 `vote_all_rounds` 内优先于 force_ship。

**BLOCKING**:无 — 全流程零人工 gate;最终人工动作只在草稿箱审阅那一刻(pipeline 外)。

**pass_flag**(frontmatter):`force_ship: true` + `force_ship_reason: "<critic_vote.py 返回的 reason>"`(force_ship 时);aborted_r18 时不写 ship 类 flag。

**理论依据(Musk × Jobs × Newton 共识)**:
- Musk: pipeline 物理上不该停 — force_ship 用 WARN 标记走数据飞轮记录,事后回查比例
- Jobs: Real Artists Ship — 到天花板就发,不无限打磨;force_ship 跟 critic_vote_pass 不同字段,审计可追
- Newton: 不变量是「最终一击在草稿箱」,中间所有 gate 都是工具不是人(含 R18-P0 自动终止)

---

## Step 7.1 · 函数预筛内文图候选

**触发**:Step 6 verdict = ship(或 6.5 partial_pass)。

**输入**:draft 全文。

**执行**:
illustrate_decider 真 CLI（`--dry-run` 跑 read_article_meta + pick_candidates,不调 LLM）:
```bash
python tools/illustrate_decider.py output/drafts/<slug>-v0.md --dry-run
```
- 预筛 H2 + 段落 ≥ 80 字,打印候选 list[Position]

**输出**:候选 list[Position](h2_idx / h2_title / position_idx / paragraph_preview / word_count)。

**pass_flag**(frontmatter):`illustration_candidates_n: 6`

---

## Step 7.2 · 花叔 Mode 2 配图决策

**触发**:Step 7.1 完成。

**输入**:draft 全文 + candidates + 可选 style_anchor。

**执行**(**严禁主线程偷懒跳过**):invoke `huashu-image-curator` skill Mode 2,输出 JSON:

⚠️ **Round 25 强制必选(2026-05-25 用户方案 A)**:**图片不再是「可选项」,也不是「0 图也合法」**。
- 不论 R20 lint 结果如何,不论 article_type 是什么,Step 7.1 → 7.2 → 7.3 必须完整执行
- **0 图路径已删**:花叔 skill 永远返回 `should_illustrate=true, count ≥ 1`(灵魂建议 0 图时也强制 1 张 fallback)
- **没调花叔就跳过 = 违规**:gate.py 强制检查 `huashu_image_curator_real_run` + `huashu_image_curator_source` 模式匹配
- **全流程不许中断**:7.1 → 7.2 → 7.3 连续执行,不在中间等用户确认
```json
{
  "should_illustrate": true,
  "count": 3,
  "style_anchor": "warm sketchnote ...",
  "image_at_h2_indices": [1, 3, 5],
  "positions": [...],
  "prompts": ["...", "...", "..."],
  "alts": [...],
  "self_check": {...}
}
```

**BLOCKING**(Round 25 升级):
- skill 不存在 → abort(不再允许 0 图 ship,旧 Round 9 决策已废)
- R18 P0 命中 prompt → abort
- skill 返回 `should_illustrate: false` → `illustrate_decider.py` 强制 placeholder fallback(双保险)

**Round 21 决策 2:封面 + 内文图风格强制一致** —
调 huashu-image-curator 之前先读 `<cover-image>.style_anchor.txt`(Step 7-cover 输出的 sidecar),把这个 anchor 作为 `style_anchor` 输入传给花叔。花叔输出的 style_anchor **必须等于或扩展自封面 anchor**(基底:warm sketchnote / cream paper #F8F0E0 / terracotta #D97757 accent / no human face / editorial illustration;**W7 删 cloud signature**),不允许另起炉灶。

```bash
# Step 7-cover 生成的 sidecar;内容作 huashu Mode 2 的 style_anchor 输入(不存在则 null)
cat output/images/<slug>-cover.style_anchor.txt
```

**pass_flag**(frontmatter):
- `huashu_decision_pass: true` + `image_decision: {<完整 JSON>}`
- **Round 22 P0-6 防伪**(必填,gate 强制):
  - `huashu_image_curator_real_run: true` — **必须真 invoke huashu-image-curator skill**
  - `huashu_image_curator_source: "huashu-image-curator Mode 2, decided count=N, style inherited from cover"` — 真实出处 + 决策摘要
- gate 看到 `huashu_decision_pass: true` 但缺这两个字段 → fake-pass 防伪触发 → 阻断 ship

---

## Step 7.3 · 内文图 Seedream 生成 + write_metadata

**触发**:Step 7.2 完成 + `should_illustrate: true` + `count > 0`。

**输入**:Step 7.2 的 decision JSON。

**执行**:
先把 Step 7.2 decision JSON 写 `output/runs/<slug>/image_decision.json`,再出图(真 CLI `illustrate_decider --generate`:内部 generate_from_decision(max_workers=3, retry_failed=True)+ write_metadata):
```bash
python tools/illustrate_decider.py --draft output/drafts/<slug>-v0.md --generate --decision output/runs/<slug>/image_decision.json --slug <slug>
```

**BLOCKING + 错误分类策略**(Round 25 升级 — placeholder fallback 替代 0 图 degraded):

`illustrate_decider._call_seedream` 把错误分四类,**Round 25 起所有失败路径都走 placeholder fallback**:

| error_type | 判定关键词 | Round 25 策略 |
|---|---|---|
| **daily_quota** | "daily" / "quota" / "quota_exceeded" / "RPD_LIMIT" / "SetLimitExceeded" / "safe experience mode" | 立即 abort retry → **`assets/placeholder-sketch.png` × N 复制到 output/images/**(不再 0 图 degraded ship) |
| **rps_limit** | "429" / "too many requests"(无 daily 字样)| retry × 2 + exponential backoff → 仍失败则 **placeholder fallback** |
| **transient** | "timeout" / "ssl" / "connection" | retry × 2 换 seed → 仍失败则 **placeholder fallback** |
| **other** | 其它(HTTP 500 / API 异常)| retry × 1 → 仍失败则 **placeholder fallback** |

**Round 25 invariant**(出口保证):`generate_from_decision` 永远不返回空 list — 任何失败路径都至少返回 N 张 placeholder(N = decision.count)。

**pass_flag**(frontmatter):
- 成功路径:
  - `image_at_h2_indices: [1, 3, 5]` ✅(从 Step 7.2)
  - `image_paths: ["output/images/<slug>-01-...png", ...]`(真图)
  - `image_generation_pass: true`
- Placeholder 路径(任何 Seedream 失败):
  - `image_at_h2_indices: [1, 3, 5]` ✅
  - `image_paths: ["output/images/<slug>-01-placeholder.png", ...]`(placeholder 副本)
  - `image_zero_reason: "seedream_daily_quota_round25_placeholder"`(或其它 reason)
  - **gate 允许 ship**(placeholder 文件 size 36 KB ≥ 5 KB threshold,通过 Newton 有效性检查)
- ❌ **不再有「0 图 degraded」路径**(Round 25 删):`image_generation_degraded: true` 会被 gate 当场拦

---

## Step 7-cover · 封面生成

**触发**:Step 6 verdict = ship(跟 Step 7.1 并行启动)。

**输入**:draft + research.md。

**执行**(W7 无模板:花叔 Mode 3 cover 自著中文 prompt → seedream_client 透传出图):
1. 抽 title/subtitle(≤14/≤22 截断;`seedream_client.py` 的 `extract_title_subtitle` 或 frontmatter)
2. invoke `huashu-image-curator` skill **Mode 3 cover**(传 article_md + title + subtitle)→ 得 JSON `{prompt(中文), aspect, style_anchor, metaphor_note}`
3. seedream_client 透传出图:
```bash
python tools/seedream_client.py \
    --prompt "<花叔的中文 prompt>" \
    --aspect <16:9|2.35:1> \
    --out output/images/<slug>-cover.png \
    --style-anchor "<style_anchor>"
```

内部流程(seedream_client 全内藏):
1. prompt **透传**(无 TEMPLATES replace)→ ARK payload
2. retry ×3 指数退避(1/2/4s)
3. 全失败 → `assets/placeholder-sketch.png` placeholder fallback(Round 25 硬约束,≥5KB)
4. 成功 → 写 sidecar(`--style-anchor` 入参,**无 cloud signature**)
- **品牌色 + 手绘风**(Style Block 锁,见 `COVER_STYLE_GUIDE.md`):暖米 #F8F0E0 底 + 陶土橙 #D97757 唯一彩 + 手绘 sketchnote + 无人物 + ≤3 视觉元素;标题走模型内渲染(轻量中文指令,**删 5 层英文加固**)

**输出**:
- `output/images/<slug>-cover.png`
- **Round 21 决策 2(W7 出图工具改 seedream_client)**:`output/images/<slug>-cover.style_anchor.txt` — sidecar 文件,给 Step 7.2 huashu-image-curator 读,确保内文图风格继承封面
  - 基底从花叔 Mode 3 的 `style_anchor` 字段写出(经 `--style-anchor` 入参),例:`"warm sketchnote hand-drawn, cream paper #F8F0E0, terracotta #D97757 accent line, no human face, editorial illustration"`(**W7 删 soft cloud signature**)

**BLOCKING**:
- cover 文件不存在 → Step 8 abort
- R18 P0 命中 prompt → abort

**pass_flag**(frontmatter):`cover_path: "output/images/<slug>-cover.png"` + `cover_pass: true`(W7 无模板,`cover_template_id` 已废;W4 banner:`cover_pass` 迁 invocation log,`cover_path` 留 frontmatter)

---

## Step 8 · 排版 + 推草稿(⛔ gate 守门)

**触发**:Step 7.3 + Step 7-cover 都完成。

**输入**:draft path + cover path + inline image paths。

**🛡️ Gate 检查**(`tools/gate.py` 由 PreToolUse hook + post_fengyun_publish preflight 双重触发):

⚠️ **W4(2026-05-27,arch-refactor-v1):pipeline-state 防伪字段全迁 invocation log**。
gate 不再查 ~25 个 frontmatter `*_pass`/`*_real_run`/`*_source`;改查 `output/runs/<slug>/*.invocation.json`。
反 fake 升级(Newton 真 invariant):`input_hash == sha256(当前 draft)` 证明这一轨评的是这一版稿。

**① frontmatter 只剩文章 metadata + 物理产物指针**(W4 精简):
```yaml
title: "..."             # ≤ 64 字
digest: "..."
author: "研究Agent的云"   # 固定
slug: "..."
date: "..."
north_star: "..."        # Step -1 产物
cover_path: "output/images/<slug>-cover.png"   # Step 7-cover,物理 check
image_paths: [...]       # Step 7.3,非空 + 每文件物理存在 + ≥ 5 KB(Round 25 硬约束)
image_at_h2_indices: [...]   # Step 7.2 产物(空 list 允许)
```

**② invocation log**(取代旧防伪字段;`output/runs/<slug>/` 下 6 件 pre-publish):

| invocation | 取代的旧 frontmatter 字段 | result |
|---|---|---|
| `iti.invocation.json` | (collect 真跑) | collected |
| `writer.invocation.json` | writer/title/ending `*_pass`+`*_real_run`+`*_source` | written |
| `verify.invocation.json` | lint_pass / wangxiaobo_* / critic_vote_pass / force_ship | ship \| force_ship |
| `critic_b_huashu.invocation.json` | critic_b_real_run / critic_b_source | ship \| no-ship \| skip |
| `critic_c_content_judge.invocation.json` | critic_c_real_run / critic_c_source | sign \| no-sign \| skip |
| `cover.invocation.json` | cover_pass / huashu_decision_pass / huashu_image_curator_* | covered |

gate 逐件查:schema 合法(`assets/run_log.schema.json`)+ `finished_at` < 1h;
**操作最终稿的 stage(verify/critic_b/critic_c/cover)额外要 `input_hash == sha256(当前 draft)`**;
`verify.result` 必须 ∈ {ship, force_ship} 才放行。

写法:每 stage 跑完调 `python tools/invocation_log.py write --slug <slug> --stage <stage> --skill <name> --input-file <file> --output <file> --result <result>`。
PostToolUse hook `validate_run_log.py` 校验写出的 invocation schema;Stop hook `ship_complete_check.py` 查 run 完整性。

**③ 外部文件物理存在性**:cover_path + 所有 image_paths 真存在 + size ≥ 5 KB。
**④ aborted_r18: true → 阻断**(R18 红线状态,留 frontmatter)。

**Gate 失败 → `sys.exit(2)` + 把 missing 打到 stderr → Claude 必须回去补**。

**执行**(gate 通过后):
```bash
# 首推 — 走 draft/add
python tools/post_fengyun_publish.py \
    output/drafts/<slug>-v0.md \
    --html-out output/render/<slug>.html

# 补内文图后重推 — 自动走 draft/update(从 frontmatter 读 media_id)
python tools/post_fengyun_publish.py \
    output/drafts/<slug>-v0.md
# 或显式传 --update-media-id <existing_media_id>
```

内部(Round 19 P0-2 + Round 21 决策 1 + Round 21 P0-17 升级,2026-05-25):
1. **layout_rules huashu 渲染(唯一活跃路径)** — Round 21 决策 1.1+1.2 砍 legacy/default/classic 分支后,任何 style 输入都强制走 huashu 模板。`--render-mode` argparse 已删除
2. **HTML 上限 60000 bytes**(Round 21 P0-17 升级,原 20000 是 layout_rules 内部历史值,无外部出处;微信真实上限 ~65000,留 5000 缓冲到 60000)
3. **fengyun_lint R12b html_size_warn**:markdown × 5 倍膨胀估算,> 50000 → warn(留 10k 到 60k 硬上限)
4. 上传封面到微信 → cover_media_id
5. 上传内文图 → 替换 markdown 里 placeholder
6. **草稿路由**(优先级):
   - CLI `--update-media-id <existing>` → 走 `cgi-bin/draft/update`,沿用原 media_id
   - frontmatter `media_id: "..."` 字段存在 → 自动走 update
   - 都没有 → 走 `cgi-bin/draft/add` 新建
7. **首推后**:自动把 `media_id` 写回 frontmatter,下次重推自动走 update
8. **update 失败兜底**:微信侧 media_id 已被清理 → 自动 fallback 到 draft/add 新建

**意义**:风云补内文图重推时,**草稿箱不会出现重复同名草稿**。原 media_id 保持稳定,审阅 + 发出动作不变。

**输出**:`media_id` 已落微信公众号草稿箱。

**pass_flag**(runlog):`{"step": 8, "media_id": "...", "render_html_path": "...", "shipped_at": "..."}`

**失败回退**:微信 API 失败 retry × 2 → 仍失败 → 报警 + 不重试。

---

## Step 9 · 报告 + audit log

**触发**:Step 8 完成。

**输入**:全程 runlog.jsonl。

**执行**:
1. 生成 `output/runs/<slug>.json` 最终报告(每 step 状态汇总)
2. 跑 `tools/verify_audit.py`(对照本 WRITE_AGENT.md 19 step 清单,缺 step 报警)
3. 打印给风云:media_id + 公众号草稿箱链接 + audit 结果

**pass_flag**:`pipeline_complete: true`

---

## 强制执行机制(双保险)

### B 主力:PreToolUse hook(物理拦截)

**`~/.claude/settings.json`** PreToolUse 块:
```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "if": "Bash(*post_fengyun_publish.py*)",
    "hooks": [{
      "type": "command",
      "command": "python D:/Dev/ai-wechat-pipeline/tools/gate.py"
    }]
  }]
}
```

`gate.py` 行为:
- 从 Bash 命令里解析出 draft 文件路径
- 读 frontmatter,检查 Step 8 要求的全部必填字段
- 检查 cover_path / image_paths 文件存在性
- 缺一 → `sys.exit(2)` + stderr 打印「缺 Step X 的 <field>,先去跑 Y 命令」
- 全通过 → exit 0

### C 兜底:post_fengyun_publish preflight assertion

`tools/post_fengyun_publish.py` `main()` 第一行调用 `gate.check_draft(draft_path)`,跟 hook 同样的检查。即使 hook 失效 / 没装 / 别的窗口跑都兜住。

### Escape hatch(紧急情况)

`gate.py` 接受 `--force-skip-gate` flag,但**只允许风云本人显式传**。日志记录每次 force-skip,审计可追。

---

## 已知 bug + Round 17 修复清单

**2026-05-25 全部修复**(代码已落地,见每行「位置 + 改动」)。

| Bug | 位置 | 严重度 | 状态 |
|---|---|---|---|
| 1 topic_recommender score 全 0 | tools/topic_recommender.py | P0 | ✅ **误诊** — cli_demo 实测正常(0.08-1.00),aihot 字段名 `title`/`summary` 跟代码一致,不存在此 bug |
| 2 title hook 软分,无 hard gate | tools/title_signal.py | P0 | ✅ 已修(Round 17 改 hard gate);**W9 supersede** — 改回软分加权(B4 hard gate 卡掉 72% 卡兹克爆款) |
| 3 classify「事件」误命中 T7 | ~~tools/generate_cover_by_template.py:78~~(W7 文件已删) | P1 | ✅ 已修(历史:删「事件」单字 → 词组);**W7 supersede** — 无模板后 classify/路由整体作废,本 bug 不再适用 |
| 4 dedup self-match Jaccard 1.0 | tools/{opening,title,ending,event}_dedup.py(W7 删 `cover_dedup.py`) | P1 | ✅ 已修(原 5 个 dedup 加 `current_draft_path` 参数 + 排除自身),**调用方须传 `current_draft_path` 才生效**;cover_dedup 已随 W7 无模板物理删除 |
| 5 lint R0 误报技术标识符 | tools/fengyun_lint.py:391 | P1 | ✅ 已修(period_pat 加 `(?![a-zA-Z0-9])` lookahead 排除扩展名) |
| 6 lint R8/R13 矛盾 | tools/fengyun_lint.py | P0 | ✅ 已修(R8 改精确 regex);**W9 supersede** — R13 整条砍(无源 craft,content-judge M6 接管),矛盾随之消失 |
| 7 fengyun_lint vs layout_rules lint 混用 | 两套 lint | P1 | ✅ 已修(两端加分工注释 + post_fengyun_publish 把 layout_rules.lint 致命级 issue 升级为 RuntimeError 阻断) |

---

## 主线程跳过环节追责机制

任何主线程 LLM 都受本宪法约束。**「我已经在历史 round 验证过,这次跳过 sanity check」是不可接受的借口**。Round 17 起:

1. 跳过任何 BLOCKING step → Step 8 gate 必然拦截
2. 试图改 frontmatter pass_flag 而不真跑前置 step → 视为 R18 P1 违规(`fake pass flag`)
3. 试图 `--force-skip-gate` → 只能风云本人在最终草稿箱审稿时显式触发,**主线程不允许自行触发**

---

## 总结一句话

**这份宪法把「请你跑完整 19 个 step」从 prose 提示词升级成了机器可执行的 invariant。Step 8 gate 是物理约束,不是劝告。**

> 文档版本:v1.0 · 2026-05-25
> 编写:Round 17 Musk × Jobs 共识 + 调研 Agent 报告
> 主要受益人:风云 + 任何接手 ship pipeline 的人(包括主线程 Claude 自己)
