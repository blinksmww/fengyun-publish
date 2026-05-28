"""
opening_signal.py — 文章开头信号评分 + PHASE1 物理约束

W9 维度重校(2026-05-27):砍 反差感/具体性/信息密度(B4 实测 6.6%/87.2%/100% — 零判别力)
+ 拆情绪锚点动词维(第一人称密度保留为物理约束)+ 真首段字数 ≥50→≥25
+ 修「首段 = 真·首段」字段名歧义(旧版把整个 intro 块当首段 → 100% 必过)。

Musk 第一性原理(2026-05-24 Round 13):
- 开头的物理目的 = 读者 0.5 秒决定继续滑屏
- 不预设「该长啥样」,只 enforce「该有什么效果」

PHASE1 数据校准:
- 跨账号同向的开头真规律 = 真实首段字数(B4 median 26 字 → 阈值 ≥25)
- TOP 5% 爆款 vs 扑街:第一人称密度 +12.5pp(强信号,物理约束保留)
- 公式新鲜度(R28):syntactic 撞型检测,W9 后唯一保留的评分维(fy 58.1% 健康)

接口:
    from tools.opening_signal import score_opening_signal

    result = score_opening_signal(text_opening)
    # {
    #   "verdict": "pass" | "redo",
    #   "physical_pass": bool,          # 真首段字数 ≥25 + 第一人称密度 ≥5
    #   "first_para_chars": int,        # 真·首段(首个空行分隔块)字数
    #   "first_person_density": float,
    #   "formula_freshness": int 0-10,  # 唯一保留评分维(R28)
    #   "weakest_dim": str,
    #   "redo_feedback": str,           # 给 writer 改稿的具体反馈
    # }
"""
from __future__ import annotations
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# 物理约束(PHASE1 数据锁定)
# ============================================================

MIN_FIRST_PARA_CHARS = 25            # W9: 50→25(B4 median 真实首段 26 字;≥50 误伤 95.6%)
MIN_FIRST_PERSON_DENSITY = 5.0       # 千字密度,实测 top 5% 爆款 +12.5pp


# ============================================================
# 公式骨架检测(R28 · Round 16 · 2026-05-25)— W9 保留的唯一评分维
# ============================================================
# 数据驱动:
#   6 篇 ship 过的文章里,4 篇套同一公式:「时间锚 + 视觉动词 + 信息名词 三件套」
#   - 教皇: 「今天凌晨,我刷推的时候,看到一条新闻」
#   - Cursor: 「昨天凌晨,Cursor 发了新模型」(时间锚)
#   - 9000 亿: 「前几天晚上,我看到一条消息」
#   - Karpathy: 「前几天,看到一条新闻,我读了三遍」
#
# H2 opening_dedup 抓不到(各篇用词不同,Jaccard 分散),
# 但公式骨架完全一样 — 用 syntactic bucket 检测能抓到

OPENING_FORMULA_BUCKETS = {
    "time_anchor": [
        "今天", "昨天", "前几天", "这两天", "这几天",
        "今天凌晨", "昨天凌晨", "前几天晚上", "前几天早上",
        "刚刚", "刚才", "前两天", "上周", "本周",
    ],
    "visual_verb": [
        "看到", "读到", "读了", "刷到", "刷推", "瞄到",
        "听到", "翻到", "盯着", "盯了", "扫到",
        "看见", "瞄了", "扫过",
    ],
    "info_noun": [
        "一条新闻", "一条消息", "一条推", "一个帖子",
        "一条推文", "一个新闻", "新闻", "消息", "推文",
        "一篇文章", "一段话",
    ],
}


def detect_opening_formula(text_first_200: str) -> dict:
    """检测开头是否套「时间锚 + 视觉动词 + 信息名词」三件套公式.

    Returns:
        {
          "hit_buckets": int,                   # 命中几个 bucket(0-3)
          "hit_details": {bucket: [hit_words]}, # 每 bucket 的命中词
          "is_formulaic": bool,                 # 是否撞公式(≥ 2 bucket 命中)
        }
    """
    hits = {}
    for bucket, words in OPENING_FORMULA_BUCKETS.items():
        bucket_hits = [w for w in words if w in text_first_200]
        if bucket_hits:
            hits[bucket] = bucket_hits

    return {
        "hit_buckets": len(hits),
        "hit_details": hits,
        "is_formulaic": len(hits) >= 2,
    }


def _score_formula_freshness(text: str) -> tuple[int, dict]:
    """公式新鲜度评分(R28).

    0 bucket 命中 → 10/10(全新公式)
    1 bucket 命中 → 8/10(单件套,边缘)
    2 bucket 命中 → 4/10(撞公式)
    3 bucket 命中 → 0/10(典型撞公式)
    """
    detect = detect_opening_formula(text)
    n = detect["hit_buckets"]
    if n == 0:
        score = 10
    elif n == 1:
        score = 8
    elif n == 2:
        score = 4
    else:  # n == 3
        score = 0
    return score, detect


# ============================================================
# 物理约束检测(PHASE1 锁定)
# ============================================================

def check_physical_constraints(full_opening_text: str) -> dict:
    """检测 PHASE1 锁定的 2 个物理约束(真首段字数 + 第一人称密度).

    Args:
        full_opening_text: 文章开头完整 intro 段落(直到第一个 H2 之前)

    Returns:
        {
          "pass": bool,
          "first_para_chars": int,       # 真·首段(首个空行分隔块)字数
          "first_person_density": float,
          "fails": list[str],
        }
    """
    # 截到 H2(## ) 之前
    intro_text = full_opening_text
    m = re.search(r"\n##\s", intro_text)
    if m:
        intro_text = intro_text[:m.start()]
    # W9 修字段名歧义(B6 Caveat):真·首段 = intro 块第一个非空段落(空行分隔),
    # 不是整个 intro 块 —— 旧版数整块字数导致 100% 必过(等于没卡)
    true_first_para = next((p for p in re.split(r"\n\s*\n", intro_text) if p.strip()), "")
    first_para_chars = len(re.sub(r"\s+", "", true_first_para))

    # 第一人称密度仍用整个 intro 块算(不扰动已验证的 81.4% 健康维)
    intro_chars = len(re.sub(r"\s+", "", intro_text))
    fp_count = len(re.findall(r"我(?!们)|我们(?!的)|笔者", intro_text))
    fp_density = (fp_count / intro_chars) * 1000 if intro_chars else 0

    fails = []
    if first_para_chars < MIN_FIRST_PARA_CHARS:
        fails.append(f"真实首段字数 {first_para_chars} < {MIN_FIRST_PARA_CHARS}(B4 median 26 字)")
    if fp_density < MIN_FIRST_PERSON_DENSITY:
        fails.append(
            f"第一人称密度 {fp_density:.1f}/千字 < {MIN_FIRST_PERSON_DENSITY}(实测 top 5% 爆款 +12.5pp)"
        )

    return {
        "pass": len(fails) == 0,
        "first_para_chars": first_para_chars,
        "first_person_density": round(fp_density, 2),
        "fails": fails,
    }


# ============================================================
# 主入口:综合评分
# ============================================================

DIM_PASS_THRESHOLD = 6  # 公式新鲜度 ≥ 6 才算通过


def score_opening_signal(text_opening: str) -> dict:
    """信号评分 + 物理约束综合评分(W9 后:物理约束 + 公式新鲜度 1 维).

    Args:
        text_opening: 文章开头(建议传前 200-300 字,或者完整 intro 段落)

    Returns: dict — 见模块顶部 docstring
    """
    text_first_200 = text_opening[:200] if len(text_opening) > 200 else text_opening

    # 物理约束(用完整 opening 算)
    phys = check_physical_constraints(text_opening)

    # 唯一保留评分维:公式新鲜度(R28)
    formula_freshness, formula_detail = _score_formula_freshness(text_first_200)

    dims = {
        "公式新鲜度 formula_freshness": formula_freshness,
    }

    # 判断每维是否通过
    failed_dims = [name for name, score in dims.items() if score < DIM_PASS_THRESHOLD]
    weakest_dim = min(dims.items(), key=lambda x: x[1])[0]

    all_dims_pass = len(failed_dims) == 0
    verdict = "pass" if (phys["pass"] and all_dims_pass) else "redo"

    # 给 writer 改稿的具体反馈
    feedback_parts = []
    if not phys["pass"]:
        feedback_parts.append("物理约束未过: " + "; ".join(phys["fails"]))
    if failed_dims:
        for fd in failed_dims:
            score = dims[fd]
            if "公式新鲜度" in fd:
                hits_str = " / ".join(
                    f"{b}({','.join(ws)})" for b, ws in formula_detail['hit_details'].items()
                )
                feedback_parts.append(
                    f"公式新鲜度 {score}/10 偏低 — 撞「时间锚+视觉动词+信息名词」三件套公式 "
                    f"[{hits_str}],换骨架 — 比如直接抛数字 / 直接进场景 / 第二人称对话"
                )

    return {
        "verdict": verdict,
        "physical_pass": phys["pass"],
        "first_para_chars": phys["first_para_chars"],
        "first_person_density": phys["first_person_density"],
        "formula_freshness": formula_freshness,
        "formula_hit_buckets": formula_detail["hit_buckets"],
        "formula_hit_details": formula_detail["hit_details"],
        "dims_pass": [n for n, s in dims.items() if s >= DIM_PASS_THRESHOLD],
        "dims_fail": failed_dims,
        "weakest_dim": weakest_dim,
        "redo_feedback": " | ".join(feedback_parts) if feedback_parts else "全过",
    }


# ============================================================
# CLI(测试用)
# ============================================================

def cli_demo():
    cases = [
        # case 1: 之前的 Anthropic 9000 亿开头
        ("Anthropic 9000 亿",
         "前几天晚上,我看到一条消息。\n\nAnthropic 这家公司,正在完成一轮 300 亿美元的融资。"
         "融完之后估值 9000 亿,反超了 OpenAI。\n\n我把这两个数字念了一遍,又念了一遍。九千亿。"
         "中国 GDP 的百分之一。\n\n第一反应当然是「这跟我有什么关系」。"),
        # case 2: 短首段(应该 fail 物理约束)
        ("短首段失败 case",
         "今天写。\n\n这是关于 AI 的。"),
        # case 3: 完全无第一人称(物理 fail)
        ("无第一人称",
         "5 月 14 日,Anthropic 公布最新融资消息。300 亿美元落地,估值 9000 亿。"
         "这件事很重要,影响整个 AI 行业。"),
    ]
    for name, text in cases:
        print(f"\n=== {name} ===")
        r = score_opening_signal(text)
        print(f"  verdict: {r['verdict']}")
        print(f"  physical: pass={r['physical_pass']} first_para={r['first_para_chars']}字 "
              f"第一人称={r['first_person_density']}/千字")
        print(f"  公式新鲜度: {r['formula_freshness']}/10")
        print(f"  公式撞型 buckets: {r['formula_hit_buckets']}/3 -> {r['formula_hit_details']}")
        print(f"  weakest: {r['weakest_dim']}")
        print(f"  feedback: {r['redo_feedback']}")


def _extract_intro_from_draft(path) -> str:
    """从 draft md 抽 intro:剥 frontmatter,取第一个 \\n## 之前(spec W6)."""
    from pathlib import Path
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]
    m = re.search(r"\n##\s", body)
    return (body[:m.start()] if m else body).strip()


def main(argv=None) -> int:
    """argparse CLI(W6 新增,只做 I/O:trial/draft → score_opening_signal → 打印 JSON).

    --trial <txt>   试稿文本(直读)
    --draft <md>    draft:剥 frontmatter + 取第一个 \\n## 前作 intro
    --demo          跑 cli_demo()
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="文章开头信号评分:trial 直读 / draft 抽 intro → score_opening_signal → 打印 JSON"
    )
    parser.add_argument("--trial", help="试稿文本文件(直读)")
    parser.add_argument("--draft", help="draft md(剥 frontmatter 抽 intro)")
    parser.add_argument("--demo", action="store_true", help="跑 cli_demo()")
    args = parser.parse_args(argv)

    if args.demo or (not args.trial and not args.draft):
        cli_demo()
        return 0

    if args.trial:
        from pathlib import Path
        text = Path(args.trial).read_text(encoding="utf-8", errors="replace")
    else:
        text = _extract_intro_from_draft(args.draft)

    result = score_opening_signal(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
