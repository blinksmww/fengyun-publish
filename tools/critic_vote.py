"""
critic_vote.py — 双轨 critic 投票决议工具(W2.C6 双轨全自动 + 隐藏天花板版,2026-05-27)

【W2.C6 架构变更(2026-05-27,arch-refactor-v1)】
  1. 删 Track A(score_draft.py 数字分)— 用户决策「彻底删」。
     质量底线从「A ≥ 60 数字分」迁移到:lint(R0-R30 机械)+ B+C 双轨灵魂共识。
  2. 双轨对等(删「C 硬否决」特殊命名):B、C 任一拒绝都 revise,不分谁。
  3. 全自动闭环 — 删 human_gate / partial_pass / auto_abort。
  4. 隐藏式 3 轮天花板(见下)。

  双轨:
    B = huashu-perspective(花叔灵魂 critic,binary ship/reject)
    C = content-judge     (风云本人 decision-time proxy,binary 挂名/不挂名)

【投票规则(评委视角 — LLM 可见,B/C 保持「严格审核」不知有上限)】
  B 过 + C 过        → ship
  任一拒绝(对等)   → revise(B reject 或 C reject 都改稿,不论谁)
  双 skip           → revise(改稿重试,不 abort)
  单 skip           → 听另一轨 verdict + 标 degraded

【隐藏式 3 轮天花板(代码层 — LLM 不可见,绝不写进任何 prompt)】
  第 3 轮 revise 后仍未双过 → 强制 ship(force_ship=True)
  - 强制 ship 的稿 frontmatter + run log 标记 force_ship: true
  - critic_vote 日志记 WARN 级别(数据飞轮回填:统计强制 ship 比例)
  - 评委 B/C 永远不知道有这个上限,prompt 保持天真严格

【R18 分级处理(全自动 — 无人工出口,与质量投票正交)】
  R18-P0(明确自指 AI 身份 = 商业机密泄漏)→ 当前稿不能 ship,但全自动处理:
    - 未到天花板 → revise(R18-P0 是 lint 可定位段,writer 删段即可自动修)
    - 到天花板仍 P0 → aborted_r18(自动终止 + ERROR 日志,不 ship 自爆稿,无人工)
    ⛔ 机密红线:force_ship 只管 B/C 质量分歧,绝不强推自爆 AI 身份的稿。
  R18-P1(架构 / skill / 工具栈暴露)→ 不阻断,走 gate tree(让 writer 改)
  R18-P2(自动化流程暴露)→ 不阻断,但计入触发率统计(给 r18_dashboard.py)

【两种调用模式】
  单轮:--b-verdict / --c-verdict        (向后兼容)
  多轮:--all-rounds <rounds.json>        (改稿循环 + 隐藏天花板)

规则参考 fengyun-publish references/stage_03_verify.md Step 6 / 6.5。
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("critic_vote")

# 隐藏天花板轮次(代码常量,绝不写进 LLM prompt)
REVISE_CEILING = 3


@dataclass
class VoteResult:
    decision: str            # ship | revise
    reason: str
    next_step: str
    b_passed: bool | None    # None 表示 skip / 缺席
    c_passed: bool | None
    degraded: dict


def _norm_binary(verdict: str | None, true_label: str) -> bool | None:
    """归一化 binary verdict 字符串:True=过 / False=否决 / None=skip"""
    if verdict is None:
        return None
    v = verdict.strip().lower()
    if v in ("", "skip", "none", "n/a", "na"):
        return None
    if v in ("yes", "y", "1", "true", "t", "pass", true_label.lower(), true_label):
        return True
    if v.startswith("no") or v in ("0", "false", "f", "fail"):
        return False
    if true_label.lower() in v:
        return True
    if "no" in v:
        return False
    return None


def _degraded_map(b, c) -> dict:
    """单 skip / 双 skip 标 degraded"""
    d = {}
    if b is None:
        d["B"] = "skip / huashu-perspective missing"
    if c is None:
        d["C"] = "skip / content-judge missing"
    return d


def gate_tree(b_verdict: str | None,
              c_verdict: str | None) -> tuple[str, str]:
    """
    双轨门控树(W2.C6 对等版,2026-05-27)

    B = huashu-perspective(花叔灵魂)/ C = content-judge(风云本人 proxy)
    返回:(decision, reason),decision ∈ {'pass', 'revise'}
    注:本函数不返回 abort(双 skip 也走 revise);abort 仅 R18-P0(在 vote_all_rounds)。

    9 组合(b/c ∈ {True ship, False reject, None skip}):
      任一 False        → revise(对等,不论谁拒绝)
      None + None       → revise(双 skip,改稿重试)
      True + True       → pass(双过)
      True+None/None+True → pass(单 skip,听 ship 轨 + degraded)
    """
    b = _norm_binary(b_verdict, "ship")
    c = _norm_binary(c_verdict, "sign")

    # 任一拒绝 → revise(双轨对等,删「C 硬否决」特殊命名)
    if b is False or c is False:
        who = []
        if b is False:
            who.append("B(花叔)")
        if c is False:
            who.append("C(风云)")
        return ("revise", f"{' + '.join(who)} reject → 改稿(任一票否决,对等)")

    # 双 skip → revise(不 abort,改稿重试)
    if b is None and c is None:
        return ("revise", "B+C 双轨皆 skip → 改稿重试(degraded)")

    # 走到这:无 reject,至少一轨 ship
    if b is True and c is True:
        return ("pass", "B ship + C ship → 双轨共识过")
    # 单 skip,听另一轨(必为 ship)
    ship_track = "B(花叔)" if b is True else "C(风云)"
    return ("pass", f"{ship_track} ship + 另一轨 skip → 听 ship 轨(degraded)")


def vote(b_verdict, c_verdict) -> VoteResult:
    """单轮投票(向后兼容旧调用)"""
    b_passed = _norm_binary(b_verdict, "ship")
    c_passed = _norm_binary(c_verdict, "sign")

    decision, reason = gate_tree(b_verdict, c_verdict)

    next_step_map = {
        "pass": "进 Step 7(封面)",
        "revise": "回 Step 6.5 改稿(看 B/C 具体段落反馈,定向修)",
    }

    # 单轮模式:pass 统一叫 ship(兼容旧 caller)
    decision_external = "ship" if decision == "pass" else decision

    return VoteResult(
        decision=decision_external,
        reason=reason,
        next_step=next_step_map[decision],
        b_passed=b_passed,
        c_passed=c_passed,
        degraded=_degraded_map(b_passed, c_passed),
    )


# ===== R18 分级检测(保留 — 与质量投票正交)=====

def check_r18_priority(lint_json_path: str | None) -> tuple[bool, list, list]:
    """
    读 lint JSON,返回 (has_p0, p1_hits, p2_hits)

    has_p0 = True 即触发 aborted_r18(阻断 force_ship,机密红线优先)
    p1_hits / p2_hits 仅用于统计/报告,不阻断 gate tree
    """
    if not lint_json_path:
        return False, [], []
    p = Path(lint_json_path)
    if not p.exists():
        return False, [], []
    try:
        lint = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return False, [], []

    has_p0 = False
    p1_hits = []
    p2_hits = []
    for v in lint.get("violations", []):
        rid = v.get("rule_id", "")
        if rid.startswith("R18_P0"):
            has_p0 = True
        elif rid.startswith("R18_P1"):
            p1_hits.append({
                "rule_id": rid,
                "issue": v.get("issue", ""),
                "matches": v.get("matches", [])[:3],
            })
        elif rid.startswith("R18_P2"):
            p2_hits.append({
                "rule_id": rid,
                "issue": v.get("issue", ""),
                "matches": v.get("matches", [])[:3],
            })
    return has_p0, p1_hits, p2_hits


# ===== 多轮模式(隐藏天花板)=====

def _summarize_round(r: dict) -> dict:
    """单轮信息摘要(用于报告)"""
    return {
        "round": r["round"],
        "draft_path": r.get("draft_path"),
        "b_verdict": r.get("b_verdict"),
        "c_verdict": r.get("c_verdict"),
        "b_passed": _norm_binary(r.get("b_verdict"), "ship"),
        "c_passed": _norm_binary(r.get("c_verdict"), "sign"),
    }


def _force_ship_result(round_info, r18_p1_warnings, r18_p2_warnings, reason):
    """
    隐藏式 3 轮天花板的强制出口(W2.C6,2026-05-27):

    第 REVISE_CEILING(3)轮 revise 后仍未双过 → 强制 ship。
      - decision=ship + force_ship=True
      - frontmatter + run log 标记 force_ship,日志 WARN
      - 评委 B/C 不知道有这个机制(prompt 永不出现「上限」)

    Real Artists Ship:全自动闭环不卡死,但留 force_ship 标记给数据飞轮回填。
    消费者(W10 体检后接上):`tools/flywheel_report.py` 扫 output/runs/ 聚合 force_ship 率 +
      花叔(B)否决率 + B/C 分歧率,产出「改 writer SOP / 选题侧,不是改这一篇」的机制层提示。
    """
    last = round_info[-1]
    logger.warning(
        "[critic_vote] FORCE SHIP — %d 轮改稿后 B/C 仍未双过,强制 ship "
        "(round=%s, draft=%s)。force_ship=true,数据飞轮回填统计。",
        REVISE_CEILING, last.get("round"), last.get("draft_path"),
    )
    return {
        "decision": "ship",
        "force_ship": True,
        "reason": (f"force_ship({REVISE_CEILING} 轮改稿后 B/C 仍未双过 → 强制 ship,"
                   f"WARN 标记):{reason}"),
        "next_step": "进 Step 7(封面)— 强制 ship 通道(force_ship 标记)",
        "chosen_version": last["round"],
        "chosen_draft_path": last.get("draft_path"),
        "r18_p1_warnings": r18_p1_warnings,
        "r18_p2_warnings": r18_p2_warnings,
        "round_info": round_info,
    }


def vote_all_rounds(rounds: list[dict]) -> dict:
    """
    多轮决议(W2.C6 双轨全自动 + 隐藏天花板,R18 也全自动 = 全流程无人工交互):
      1. 末轮 lint R18-P0(明确自指 AI = 商业机密泄漏)→ 当前稿不能 ship:
           未到天花板 → revise(R18-P0 是 lint 可定位段,writer 删段即可自动修)
           到天花板仍 P0 → aborted_r18(自动终止 + ERROR 日志,不 ship 自爆稿,**无人工**)
      2. 末轮无 P0 → 双轨 gate tree:
           pass → ship(critic_vote_pass)
           revise + N < 天花板 → revise(继续改,评委不知有上限)
           revise + N >= 天花板 → 强制 ship(force_ship=true + WARN)

    全流程无人工交互:R18-P0 不再「停 + 甩人工」,改 revise 自动修 / 改不掉自动终止。
    唯一人工动作是 pipeline 之外的「风云草稿箱审阅 + 点发出」(NORTH_STAR)。
    """
    if not rounds:
        return {
            "decision": "abort",
            "reason": "rounds 为空",
            "next_step": "至少给一轮数据",
            "round_info": [],
        }

    # R18-P1 / P2 跨轮统计(不阻断,给 r18_dashboard.py)
    r18_p1_warnings = []
    r18_p2_warnings = []
    for r in rounds:
        _, p1, p2 = check_r18_priority(r.get("lint_json_path"))
        if p1:
            r18_p1_warnings.append({"round": r["round"], "hits": p1})
        if p2:
            r18_p2_warnings.append({"round": r["round"], "hits": p2})

    round_info = [_summarize_round(r) for r in rounds]
    last = rounds[-1]

    # 1. R18-P0 红线检查(只看末轮 = 当前稿;早轮 P0 若已改掉就不算)
    last_has_p0, _, _ = check_r18_priority(last.get("lint_json_path"))
    if last_has_p0:
        if last["round"] >= REVISE_CEILING:
            # 改到天花板还在自爆 AI 身份 → 自动终止(绝不 ship 机密泄漏稿),ERROR 日志,无人工
            logger.error(
                "[critic_vote] ABORTED_R18 — %d 轮改稿后末轮仍命中 R18-P0(自指 AI 身份),"
                "自动终止不 ship(draft=%s)。商业机密红线,force_ship 不适用。",
                REVISE_CEILING, last.get("draft_path"),
            )
            return {
                "decision": "aborted_r18",
                "reason": (f"R18-P0(明确自指 AI 身份 = 商业机密泄漏)改到天花板"
                           f"({REVISE_CEILING} 轮)仍未消除 → 自动终止,不 ship 自爆稿。"),
                "next_step": "自动终止 pipeline(无人工)。ERROR 日志留档,cron 下轮选别的主题。",
                "r18_p1_warnings": r18_p1_warnings,
                "r18_p2_warnings": r18_p2_warnings,
                "round_info": round_info,
            }
        # 未到天花板 → 走 revise 自动修(R18-P0 是机械可定位段,writer 删/重写即可)
        return {
            "decision": "revise",
            "reason": ("末轮 lint 命中 R18-P0(自指 AI 身份)→ 改稿删/重写该段"
                       "(lint matches 给了具体 ctx,机械可定位,自动修)"),
            "next_step": f"回 Step 6.5 改稿(round {last['round']+1}),优先删 R18-P0 段",
            "r18_p0_in_last": True,
            "r18_p1_warnings": r18_p1_warnings,
            "r18_p2_warnings": r18_p2_warnings,
            "round_info": round_info,
        }

    # 2. 末轮无 P0 → 双轨门控树
    decision, reason = gate_tree(last.get("b_verdict"), last.get("c_verdict"))

    if decision == "pass":
        return {
            "decision": "ship",
            "reason": reason,
            "next_step": "进 Step 7(封面)",
            "chosen_version": last["round"],
            "chosen_draft_path": last.get("draft_path"),
            "r18_p1_warnings": r18_p1_warnings,
            "r18_p2_warnings": r18_p2_warnings,
            "round_info": round_info,
        }

    # decision == "revise"
    # N < 3 → 继续改(评委不知有上限);N >= 3 → 隐藏天花板强制 ship
    if last["round"] >= REVISE_CEILING:
        return _force_ship_result(
            round_info, r18_p1_warnings, r18_p2_warnings, reason,
        )
    return {
        "decision": "revise",
        "reason": reason,
        "next_step": f"回 Step 6.5 改稿(round {last['round']+1})",
        "r18_p1_warnings": r18_p1_warnings,
        "r18_p2_warnings": r18_p2_warnings,
        "round_info": round_info,
    }


def main():
    ap = argparse.ArgumentParser(
        description="critic 双轨投票决议(W2.C6 全自动 + 隐藏天花板版)")
    ap.add_argument("--b-verdict", default=None,
                    help="(单轮)ship / no-ship / skip(huashu-perspective)")
    ap.add_argument("--c-verdict", default=None,
                    help="(单轮)sign / no-sign / skip(content-judge)")
    ap.add_argument("--all-rounds", default=None,
                    help="(多轮)JSON 文件路径,含 rounds")
    ap.add_argument("--out", default=None, help="JSON 输出路径")
    ap.add_argument("--verbose", action="store_true", help="打开 WARN 日志输出")
    args = ap.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

    if args.all_rounds:
        rounds_data = json.loads(Path(args.all_rounds).read_text(encoding="utf-8"))
        rounds = rounds_data["rounds"]
        result = vote_all_rounds(rounds)

        print(f"=== critic vote · multi-round ({len(rounds)} rounds) ===")
        print(f"decision: {result['decision'].upper()}")
        if result.get("force_ship"):
            print(f"          ↳ force_ship(隐藏 3 轮天花板:强制 ship + WARN 标记)")
        print(f"reason:   {result['reason']}")
        print(f"next:     {result['next_step']}")
        if "chosen_version" in result:
            print(f"chosen:   round {result['chosen_version']} → "
                  f"{result.get('chosen_draft_path')}")
        print(f"\nround info:")
        for s in result["round_info"]:
            print(f"  round {s['round']}: "
                  f"B={s['b_verdict']} C={s['c_verdict']}")
        if result.get("r18_p1_warnings"):
            total = sum(len(w["hits"]) for w in result["r18_p1_warnings"])
            print(f"\n⚠️  R18-P1(架构暴露,已计入 revise):"
                  f" {total} hits across {len(result['r18_p1_warnings'])} rounds")
        if result.get("r18_p2_warnings"):
            total = sum(len(w["hits"]) for w in result["r18_p2_warnings"])
            print(f"💭 R18-P2(自动化暴露,计入统计):"
                  f" {total} hits across {len(result['r18_p2_warnings'])} rounds")

        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\nJSON: {args.out}")

        exit_map = {"ship": 0, "revise": 1, "abort": 2, "aborted_r18": 4}
        sys.exit(exit_map.get(result["decision"], 2))

    # 单轮模式
    r = vote(args.b_verdict, args.c_verdict)
    print(f"=== critic vote · single round ===")
    print(f"B:        {args.b_verdict}  -> {r.b_passed}")
    print(f"C:        {args.c_verdict}  -> {r.c_passed}")
    print(f"decision: {r.decision.upper()}")
    print(f"reason:   {r.reason}")
    print(f"next:     {r.next_step}")
    if r.degraded:
        print(f"degraded: {r.degraded}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(asdict(r), ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"\nJSON: {args.out}")

    exit_map = {"ship": 0, "revise": 1}
    sys.exit(exit_map.get(r.decision, 2))


if __name__ == "__main__":
    main()
