# Wave 8: ITI I-2 + TrendRadar wrapper

> **模式**:你单干(单写者)+ explorer(Sonnet 只读,完工)辅助;不 fan-out。
> **WHY 出处**:`docs/ARCH_REFACTOR_V1_PLAN.md` §阶段 E(E1-E4)+ §7.4:563-564(信源风险兜底)。
> **3 个 fork 已拍板**(2026-05-27,AskUserQuestion):① per-feed N=5(暴露 `--per-feed-n` flag,默认值)② **砍** smol.ai by-topic ③ E4 = no-op + 文档记录。
> **纪律**:test-first(改采集/解析必有测试,W6/W7 同款)+ 0 改无关业务逻辑 + 物理删 .py 后清 .pyc(本 wave 不删 .py)+ 反 p-hacking(N=5 是采集广度旋钮非 critic 阈值,不在 corpus grid search)。

---

## 物理目的(一句话)

把 TrendRadar 信源从「只读 `latest_daily.md` markdown 摘要 ~170 条」升级为「直接读 `output/rss/<date>.db` 全量、按 feed 维度取最新 N=5 条」(抓不到则 try/except 回退旧 markdown reader);I-2 深搜不再镜像 I-1 的 4 个 generic WebSearch query,改为「WebFetch T 选定 topic 的主源 URL + aihot `?q=` 实体搜索 + 1 个补充 query」。

---

## 改动文件清单(精确到行号)

### 代码(test-first)

**`tools/iti_collect.py`**
- L47-58 常量区:新增 `TRENDRADAR_RSS_DIR = Path(r"D:\Dev\TrendRadar\output\rss")` + `TRENDRADAR_PER_FEED_N = 5`。
- L93 之后(`fetch_aihot` 结尾):新增 **E3a** `fetch_aihot_by_query(entities, take=15) -> list[dict]`(逐 entity[:3] 调 `?q=<entity>` 合并去重,复用 `fetch_aihot` 的 UA + ssl + 字段映射,`source="aihot:q:<entity>"`,`_origin="aihot"`)。
- L205-232 `fetch_trendradar()`:**E2 三拆**——
  - L210-232 现 markdown body → 抽成 `_fetch_trendradar_markdown(max_age_hours=36)`(零改逻辑,纯改名)。
  - 新增 `_fetch_trendradar_db(per_feed_n=5, max_age_hours=36)`:glob `TRENDRADAR_RSS_DIR/*.db`,按 mtime 取最新一个;mtime > max_age_hours → 返回 `[]`(触发回退);`sqlite3.connect(uri ro)` + window function `ROW_NUMBER() OVER (PARTITION BY feed_id ORDER BY published_at DESC)` 取每 feed 前 N;映射成标准 dict;**整体 try/except → 失败返回 `[]`**(触发回退)。
  - 新 `fetch_trendradar(per_feed_n=TRENDRADAR_PER_FEED_N, max_age_hours=36)`:`db = _fetch_trendradar_db(...)`;`if db: return db`;`else: return _fetch_trendradar_markdown(...)`(stderr 打印走了哪条路)。
- L394-399 `collect_pool(...)` 签名:加 `per_feed_n: int = TRENDRADAR_PER_FEED_N`。
- L422 source lambda:`("trendradar", lambda: fetch_trendradar())` → `("trendradar", lambda: fetch_trendradar(per_feed_n=per_feed_n))`。
- L482-491 `cli()`:加 `--per-feed-n`(type=int,default=`TRENDRADAR_PER_FEED_N`),透传 `collect_pool(per_feed_n=args.per_feed_n)`。

**`tools/iti_explore.py`**(E3a 接线)
- L289 之后(`fetch_trendradar_topic` 结尾)新增 `_fetch_aihot_by_query(entities)` 薄 wrapper(沿用 L266-272 `sys.path.insert + from iti_collect import` 模式,import 失败返回 `[]`)。
- L377-384 explore_topic 源列表:在 `("trendradar", ...)` 后(第 3 位)插 `("aihot-query", lambda: _fetch_aihot_by_query(entities))`。理由:aihot `?q=` 是实体定向 + 7 天新鲜的高价值源,「够用就停」前置。

**新建 `tools/test_iti_collect_trendradar.py`**(当前无 `test_iti_collect.py`,test-first)
- E2 DB reader:`tmp_path` 建临时 sqlite(2 feed × 4 item),断言 `per_feed_n=2` 每 feed 返 2 条、按 `published_at DESC`、dict shape/source 正确。
- E2 回退:无 DB / 空 DB / DB 过期 → `fetch_trendradar` 回退到 markdown(monkeypatch `TRENDRADAR_LATEST` 指 tmp 文件,断言拿 markdown 条目)。
- E2 优先级:DB 有数据时 `fetch_trendradar` 返 DB 条目(不读 markdown)。
- E3a `fetch_aihot_by_query`:monkeypatch `urllib.request.urlopen` 返假 JSON,断言字段映射 + 逐 entity 合并 + URL 去重。**全 mock,零真网络,零触碰真 `D:\Dev\TrendRadar`**。

### 文档(doc-sync §8.7 + vendor 镜像)

- `~/.claude/skills/fengyun-publish/references/stage_01_collect.md`:
  - L17(「TrendRadar 旧时丢 67 feed 覆盖」)→ 改述 DB reader 按 feed 取最新 N 条 + 过期才回退 markdown。
  - L189 + L193-196(**E1**:「两个 I 都用 WebSearch / 中英文各 ≥ 2 次」+ 4 generic query)→ 改为 I-2 = WebFetch 主源 URL(`--main-source-urls`)+ aihot `?q=` 实体搜索 + **1** 个补充 topic query,不再镜像 I-1。
- `~/.claude/skills/fengyun-publish/SKILL.md` L54(「主线程 WebSearch 中英文各 2 次(I-1 + I-2 都不能漏)」)→ I-1 = 4 generic;I-2 = WebFetch 主源 + 1 补充 query。
- `D:\Dev\ai-wechat-pipeline\WRITE_AGENT.md` L428(「WebSearch ≥ 4 次(中英文各 2 次)」)+ L447(`websearch_count: 4`)→ I-2 = 主源 WebFetch + aihot `?q=` + 1 补充 query。
- vendor 镜像(§8.6):`cp` user-level → `vendor/skills/fengyun-publish/{SKILL.md,references/stage_01_collect.md}`。

### 不动(敢砍 / 已完成 / 越界)

- **E3b smol.ai by-topic**:**砍**(fork 拍板)。`fetch_smol_ai()`(iti_collect L287)给 I-1 广搜不动。
- **E4**:5 僵尸 RSS 已删(2026-05-26)、X 从未进 ITI、IT之家 只在 `D:\Dev\TrendRadar\config.yaml`(跨仓库不被本分支 git 跟踪)→ no-op,本 spec 记录即可。
- `fetch_trendradar_topic()`(iti_explore L249):E3 已完成(前次会话),6 测试覆盖,**不动**。

---

## 改前 vs 改后(代码 diff 样例)

**E2 `fetch_trendradar` 编排(iti_collect.py)**
```python
# 改前 (L205-232):只读 markdown
def fetch_trendradar(max_age_hours: int = 36) -> list[dict]:
    if not TRENDRADAR_LATEST.exists(): return []
    ... mtime/age 检查 ...
    for m in _TRENDRADAR_LINK_PATTERN.finditer(text): out.append({...})
    return out

# 改后:DB 优先,markdown 兜底
def _fetch_trendradar_markdown(max_age_hours: int = 36) -> list[dict]:
    # ← 原 L210-232 整块逻辑,零改
    ...

def _fetch_trendradar_db(per_feed_n: int = 5, max_age_hours: int = 36) -> list[dict]:
    try:
        dbs = sorted(TRENDRADAR_RSS_DIR.glob("*.db"), key=lambda p: p.stat().st_mtime)
        if not dbs: return []
        newest = dbs[-1]
        if datetime.now() - datetime.fromtimestamp(newest.stat().st_mtime) > timedelta(hours=max_age_hours):
            return []
        con = sqlite3.connect(f"file:{newest}?mode=ro", uri=True)
        rows = con.execute(
            "SELECT title,url,summary,published_at,feed_id,name FROM ("
            " SELECT ri.title,ri.url,ri.summary,ri.published_at,ri.feed_id,rf.name,"
            " ROW_NUMBER() OVER (PARTITION BY ri.feed_id ORDER BY ri.published_at DESC) rn"
            " FROM rss_items ri LEFT JOIN rss_feeds rf ON ri.feed_id=rf.id"
            ") WHERE rn<=?", (per_feed_n,)).fetchall()
        con.close()
        return [{"title": r[0], "summary": r[2] or "", "url": r[1],
                 "source": f"trendradar:{r[5] or r[4]}", "category": None,
                 "publishedAt": r[3], "_origin": "trendradar"} for r in rows]
    except Exception as e:
        print(f"  [trendradar db] {e}", file=sys.stderr); return []

def fetch_trendradar(per_feed_n: int = TRENDRADAR_PER_FEED_N, max_age_hours: int = 36) -> list[dict]:
    db = _fetch_trendradar_db(per_feed_n=per_feed_n, max_age_hours=max_age_hours)
    if db:
        print(f"  [trendradar] DB reader: {len(db)} 条 ({per_feed_n}/feed)", file=sys.stderr)
        return db
    print("  [trendradar] DB 空/过期/失败,回退 markdown reader", file=sys.stderr)
    return _fetch_trendradar_markdown(max_age_hours=max_age_hours)
```

**E3a `fetch_aihot_by_query`(iti_collect.py,新增)**
```python
def fetch_aihot_by_query(entities: list[str], take: int = 15) -> list[dict]:
    """aihot ?q= server-side 关键词搜索(title+中文title+中文summary,见 aihot/SKILL.md L184-206)."""
    out, seen = [], set()
    for ent in [e for e in entities if e][:3]:
        url = f"https://aihot.virxact.com/api/public/items?q={urllib.parse.quote(ent)}&take={take}"
        req = urllib.request.Request(url, headers={"User-Agent": UA_DEFAULT})
        try:
            with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=20) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"  [aihot q={ent}] {e}", file=sys.stderr); continue
        for it in data.get("items", []):
            u = it.get("url", "")
            if u in seen: continue
            seen.add(u)
            out.append({"title": it.get("title",""), "summary": it.get("summary") or "",
                        "url": u, "source": f"aihot:q:{ent}", "category": it.get("category"),
                        "publishedAt": it.get("publishedAt"), "_origin": "aihot"})
    return out
```

**E1 I-2 doc(stage_01_collect.md L193-196)**
```text
# 改前
1. 主线程必跑 WebSearch(I-2 不能漏,中英文各 ≥ 2 次):
   - 中文:<title> 中文 最新 / <title> 影响 分析
   - 英文:<title_en> latest analysis / <entities[0]> <entities[1]> news
# 改后
1. I-2 不再镜像 I-1 的 4 个 generic query。深搜 = 三路:
   - WebFetch:T 选定候选的主源 url(chosen.json 的 chosen.url)→ --main-source-urls
   - aihot ?q=:explore_topic 已内置 aihot-query 源(实体定向,7 天窗)
   - 主线程补 1 个 topic-specific WebSearch query(只补,不重跑 I-1 的 4 个)
```

---

## 验收命令(本 wave 专有)

```bash
# 1. 零回归基线(≥ 180 passed;新增 test_iti_collect_trendradar.py 后总数上升)
python -X utf8 scripts/verify_baseline.py

# 2. W8 专有:整目录 pytest(W7 教训:本 wave 不删 .py,无 .pyc 孤儿风险)
python -X utf8 -m pytest tools/test_iti_collect_trendradar.py tools/test_iti_explore.py -q

# 3. trendradar DB reader 真读到全量 feed(有真 DB 时;无则回退 markdown,二者都不崩)
python -X utf8 tools/iti_collect.py --hours 24 --no-write --per-feed-n 5

# 4. I-2 不再 4 query:确认 explore_topic stats 含 aihot-query 源
python -X utf8 tools/iti_explore.py demo "demo" --entities Anthropic Claude

# 5. 旧 22 源/markdown fallback 可触发:DB 不存在/过期时 fetch_trendradar 回退(test 2 已覆盖,真机可改名 rss/ 验证)

# 6. --help 不崩
python -X utf8 tools/iti_collect.py --help
python -X utf8 tools/iti_explore.py --help
```

**验收守门**:verify_baseline 零回归(≥ 180 passed)+ W8 专有(DB reader 真读到 per-feed 数据 / I-2 含 aihot-query / fallback 可触发)+ 工具 `--help`/`--no-write` 不崩。

---

## 风险 + 兜底(本 wave 专有)

| 风险 | 兜底 |
|---|---|
| TrendRadar DB schema 跟真机不符 / sqlite 无 window function | `_fetch_trendradar_db` 整体 try/except → 返 `[]` → 自动回退 markdown reader(ARCH §7.4:563)。Python 3.25+ sqlite 支持 window function;真机 sqlite 版本兜底由 try/except 接住 |
| `published_at` 非 ISO(部分 feed RFC2822/空)导致 DESC 排序错乱 | 仅影响「每 feed 取哪 5 条」精度,不影响正确性;NULL 在 SQLite DESC 排最后;广搜池后续 dedup/rank 收口,可接受 |
| aihot `?q=` 限流 / 沙盒无网络 | `fetch_aihot_by_query` 逐 entity try/except continue;explore_topic 该源失败不影响其他源(L397-400 已有);ARCH §7.4:564 = 降级 daily 接口(已有 `fetch_aihot`) |
| 读真 DB 触碰跨仓库 `D:\Dev\TrendRadar` | **只读**(`mode=ro`);测试用 tmp sqlite 不碰真机;不写 TrendRadar |
| 沙盒拒 subagent Bash | 主线程动态轨兜底跑 verify,commit message 诚实标注(§8.5.2) |
| 改 fetch_trendradar 影响 `fetch_trendradar_topic`(iti_explore L274 调它) | 签名向后兼容(per_feed_n 有默认值,旧调用 `fetch_trendradar(max_age_hours=...)` 仍可);test_iti_explore.py 6 个 trendradar_topic 测试做回归守门 |

**E4 状态记录**(no-op 依据 fork 拍板):5 僵尸 RSS 已删 / X 从未进 ITI 工具 / IT之家 仅在跨仓库 TrendRadar config.yaml(本分支 git 不跟踪,反爬死路时 DB 自然无其条目)→ 本分支不动任何代码/配置。

---

## reviewer subagent prompt(全新 session 审稿用)

> 你是 W8 的 reviewer(全新 session,不知道主线程怎么写的)。仓库 `D:\Dev\ai-wechat-pipeline` 分支 `arch-refactor-v1`。只读审 `git diff a12dd19..HEAD`(W8 commit)+ 本 spec。输出 binary verdict:**SHIP / REVISE**,列 P0(阻断)/P1/P2。重点核:
> 1. **0 改无关业务逻辑**:`_fetch_trendradar_markdown` 是否原 markdown 逻辑零改名抽取?`collect_pool` 除 `per_feed_n` 透传外打分/dedup/rank 是否未动?`fetch_aihot_by_query` 是否复用 `fetch_aihot` 字段映射不发明新逻辑?
> 2. **test-first 真做**:`test_iti_collect_trendradar.py` 是否覆盖 DB reader + 回退 + 优先级 + aihot mock?是否全 mock 零真网络、零触碰真 `D:\Dev\TrendRadar`?
> 3. **回退真可触发**:DB 空/过期/sqlite 异常 → 是否真回退 markdown(非崩溃/非空)?try/except 是否吞掉所有 DB 异常?
> 4. **向后兼容**:`fetch_trendradar` 新签名是否不破坏 `iti_explore.fetch_trendradar_topic`(L274)?test_iti_explore.py 是否仍全过?
> 5. **scope 无越界**:是否误删/误改 smol.ai、误动 TrendRadar config、误删 .py?E4 是否如 spec 所述 no-op?
> 6. **doc-sync §8.7**:stage_01_collect / SKILL / WRITE_AGENT 的 I-2「4 query」描述是否真改成「主源 WebFetch + aihot ?q= + 1 补充 query」?vendor/ 镜像是否 byte-identical 同步?有无残留「中英文各 2 次」活引用(grep)?
> 7. **反 p-hacking**:N=5 是否仅作采集广度默认值 + CLI flag,无 corpus grid search?
