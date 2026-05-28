"""flywheel_report.py — force_ship 学习回路消费者(arch-refactor-v1 post-W10 follow-up,2026-05-27)。

物理目的(闭合 invariant #4「0 消费者 = 0 生产」):W10 全系统体检发现 critic_vote 写的
force_ship 标记 + critic B/C verdict 此前**无任何消费者**(weekly_metrics 归档、critic_retrain 没建),
学习信号死在 JSON 里——pipeline「会跑」但「不会自己变好」。本工具是第一个真消费者:扫 output/runs/
的 W4 invocation log,聚合 force_ship 率 + 花叔(B)否决率 + content-judge(C)挂名率 + B/C 结构性
分歧率,产出 markdown 报告,指导「改 writer SOP / 选题侧,而不是改这一篇」(feedback_iterate_mechanism_not_article)。

数据源:**只读 W4 invocation log**(output/runs/<slug>/{verify,critic_b_huashu,critic_c_content_judge}.invocation.json,
schema 稳定)。历史顶层 run 报告(output/runs/<date>-<slug>.json)跨 Round schema 不一致(老 3 轨
critic_A/B/C_verdict / 半截 steps dict / 新 force_ship),不可靠聚合,**本工具不解析**(诚实 scope 决策;
新架构的标准数据从 W10 起才开始累积)。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
RUNS_ROOT = ROOT / "output" / "runs"

# B(花叔 huashu)否决 = no-ship;C(content-judge)挂名 = sign;verify 决议强制 ship = force_ship。
_B_REJECT = {"no-ship", "no_ship", "reject", "redo"}
_C_SIGN = {"sign"}
_FORCE_SHIP = {"force_ship"}


def _load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def scan_runs(runs_root: Path | None = None) -> list[dict]:
    """扫 invocation log 聚合每个 slug 的 verify/B/C result。

    只认有 verify.invocation.json 的 slug 目录(= 一次走完决议的标准 ship);
    没 verify 的目录(_w10stage / observation 等中间产物)跳过。
    """
    runs_root = runs_root or RUNS_ROOT
    records: list[dict] = []
    if not runs_root.exists():
        return records
    for d in sorted(p for p in runs_root.iterdir() if p.is_dir()):
        verify = _load_json(d / "verify.invocation.json")
        if not verify:
            continue
        b = _load_json(d / "critic_b_huashu.invocation.json") or {}
        c = _load_json(d / "critic_c_content_judge.invocation.json") or {}
        records.append({
            "slug": d.name,
            "source": "invocation",
            "verify_result": verify.get("result", ""),
            "b_result": b.get("result", ""),
            "c_result": c.get("result", ""),
        })
    return records


def aggregate(records: list[dict]) -> dict:
    """聚合 force_ship 率 / B 否决率 / C 挂名率 / B-C 分歧率。空集不除零。"""
    n = len(records)
    force = sum(1 for r in records if r.get("verify_result") in _FORCE_SHIP)
    b_reject = sum(1 for r in records if r.get("b_result") in _B_REJECT)
    c_sign = sum(1 for r in records if r.get("c_result") in _C_SIGN)
    # B/C 结构性分歧 = 一轨想 ship、另一轨不想(只在两轨 result 都有时计)。
    disagree = sum(
        1 for r in records
        if r.get("b_result") and r.get("c_result")
        and ((r["b_result"] not in _B_REJECT) != (r["c_result"] in _C_SIGN))
    )

    def _rate(x: int) -> float:
        return (x / n) if n else 0.0

    return {
        "n": n,
        "force_ship_count": force, "force_ship_rate": _rate(force),
        "b_reject_count": b_reject, "b_reject_rate": _rate(b_reject),
        "c_sign_count": c_sign, "c_sign_rate": _rate(c_sign),
        "bc_disagree_count": disagree, "bc_disagree_rate": _rate(disagree),
    }


def render_report(agg: dict, records: list[dict]) -> str:
    lines = ["# force_ship 学习回路报告(flywheel)", ""]
    n = agg["n"]
    if n == 0:
        lines.append("暂无标准 ship 记录(output/runs/<slug>/ 下无 verify.invocation.json)。")
        lines.append("新架构的标准数据从 W10 起累积,跑几篇 /ship 后再看趋势。")
        return "\n".join(lines)
    lines += [
        f"- 标准 ship 记录:**{n}** 篇",
        f"- force_ship 率:**{agg['force_ship_count']}/{n} = {agg['force_ship_rate']:.0%}**",
        f"- 花叔(B)否决率:{agg['b_reject_count']}/{n} = {agg['b_reject_rate']:.0%}",
        f"- content-judge(C)挂名率:{agg['c_sign_count']}/{n} = {agg['c_sign_rate']:.0%}",
        f"- B/C 结构性分歧率:{agg['bc_disagree_count']}/{n} = {agg['bc_disagree_rate']:.0%}",
        "",
        "## force_ship 篇目(花叔到天花板仍否,代码层强制 ship)",
    ]
    fs = [r for r in records if r.get("verify_result") in _FORCE_SHIP]
    if fs:
        lines += [f"- `{r['slug']}`(B={r.get('b_result') or '?'} / C={r.get('c_result') or '?'})" for r in fs]
    else:
        lines.append("- (无)")
    lines += ["", "## writer SOP 提示(迭代机制,不是改这一篇)"]
    if agg["force_ship_rate"] >= 0.5:
        lines += [
            "- ⚠️ force_ship 率 ≥ 50%:花叔的 emotion 门槛跟当前选题 / 文体**系统性不匹配**。",
            "  机制层选项:① 选题侧多挑能写真 lived-stake 的题(花叔吃这套)② 或接受思想 / 分析型文章常态 "
            "force_ship,把花叔降级为「改稿建议源」而非 ship 闸门。**别靠改这一篇硬凑 emotion**。",
        ]
    elif n < 5:
        lines.append(f"- 样本偏少(n={n}),先攒到 ≥5 篇再看趋势,避免单篇噪声。")
    else:
        lines.append("- force_ship 率正常,双轨闸门有效,暂无需调 writer SOP。")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="force_ship 学习回路消费者:聚合 critic B/C verdict + force_ship 出报告")
    ap.add_argument("--runs-root", default=str(RUNS_ROOT))
    ap.add_argument("--out", default=None, help="markdown 输出路径(默认打印 stdout)")
    args = ap.parse_args()
    records = scan_runs(Path(args.runs_root))
    md = render_report(aggregate(records), records)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"✅ 写入 {args.out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
