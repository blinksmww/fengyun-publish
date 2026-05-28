"""
test_round26_fixes.py — Round 26 + W2.C6 修复的单元测试

覆盖:
  A. critic_vote.vote_all_rounds(W2.C6 双轨全自动 + 隐藏天花板,2026-05-27 重写):
     双轨对等(任一 reject → revise)/ 双 skip → revise / 单 skip → 听另一轨
     隐藏 3 轮天花板:第 3 轮 revise 后仍未双过 → force_ship
  B. fix_punctuation:6 个用例(配对引号 / 中文间标点 / 代码块跳过 / frontmatter 跳过)
  (C. opening_signal._score_reframe — W9 删:反差感维已砍,对应测试随之移除)

Round 26 SPEC: docs/SPEC_ROUND26_HUMAN_GATE_FIX.md
W2.C6 SPEC: 删 Track A(score_draft)+ human_gate/partial_pass/auto_abort,
            评委不知有上限,代码层隐藏 3 轮天花板强制 ship。
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import critic_vote
import fix_punctuation


# ============================================================
# A. critic_vote — W2.C6 双轨全自动 + 隐藏天花板(2026-05-27 重写,删 Track A)
# ============================================================

def test_a1_b_reject_single_round_goes_revise():
    """B=no-ship + C=ship 单轮 → revise(任一票否决,不能 ship)"""
    rounds = [{
        "round": 1,
        "draft_path": "draft_v1.md",
        "b_verdict": "no-ship",
        "c_verdict": "ship",
        "lint_json_path": None,
    }]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "revise", \
        f"B reject 单轮必须 revise,实际 {r['decision']}: {r['reason']}"
    assert "round 2" in r["next_step"], f"应该提示进 round 2,实际 {r['next_step']}"
    assert not r.get("force_ship"), "单轮不该 force_ship"
    print("  ✅ A1: B reject single round → revise")


def test_a2_b_reject_three_rounds_force_ship():
    """3 轮仍 B reject → 隐藏天花板 force_ship(评委不知有上限)"""
    rounds = [
        {"round": 1, "b_verdict": "no-ship", "c_verdict": "ship",
         "draft_path": "d1.md", "lint_json_path": None},
        {"round": 2, "b_verdict": "no-ship", "c_verdict": "ship",
         "draft_path": "d2.md", "lint_json_path": None},
        {"round": 3, "b_verdict": "no-ship", "c_verdict": "ship",
         "draft_path": "d3.md", "lint_json_path": None},
    ]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship", \
        f"3 轮 revise 后应 force_ship → ship,实际 {r['decision']}"
    assert r.get("force_ship") is True, "必须标记 force_ship=True"
    assert r.get("chosen_version") == 3
    print("  ✅ A2: 3 轮 revise 后 → force_ship ship")


def test_a3_c_reject_three_rounds_force_ship():
    """3 轮仍 C reject(对等,无硬否决特权)→ 同样 force_ship"""
    rounds = [
        {"round": 1, "b_verdict": "ship", "c_verdict": "no-sign",
         "draft_path": "d1.md", "lint_json_path": None},
        {"round": 2, "b_verdict": "ship", "c_verdict": "no-sign",
         "draft_path": "d2.md", "lint_json_path": None},
        {"round": 3, "b_verdict": "ship", "c_verdict": "no-sign",
         "draft_path": "d3.md", "lint_json_path": None},
    ]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship", \
        f"3 轮 C reject 后也应 force_ship(对等),实际 {r['decision']}"
    assert r.get("force_ship") is True
    print("  ✅ A3: 3 轮 C reject 后 → force_ship(双轨对等,无硬否决特权)")


def test_a4_double_skip_revise_not_abort():
    """B skip + C skip 单轮 → revise(W2.C6 改:不 abort)"""
    rounds = [{"round": 1, "b_verdict": "skip", "c_verdict": "skip",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "revise", \
        f"双 skip 单轮应 revise(不 abort),实际 {r['decision']}"
    print("  ✅ A4: 双 skip 单轮 → revise(不 abort)")


def test_a5_double_skip_three_rounds_force_ship():
    """B/C 都 skip 跑满 3 轮 → force_ship(全自动闭环不卡死)"""
    rounds = [
        {"round": 1, "b_verdict": "skip", "c_verdict": "skip",
         "draft_path": "d1.md", "lint_json_path": None},
        {"round": 2, "b_verdict": "skip", "c_verdict": "skip",
         "draft_path": "d2.md", "lint_json_path": None},
        {"round": 3, "b_verdict": "skip", "c_verdict": "skip",
         "draft_path": "d3.md", "lint_json_path": None},
    ]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship" and r.get("force_ship") is True
    print("  ✅ A5: 双 skip 3 轮 → force_ship")


def test_a6_c_reject_single_round_revise():
    """C reject 单轮 → revise(对等,B ship 不覆盖)"""
    rounds = [{"round": 1, "b_verdict": "ship", "c_verdict": "no-sign",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "revise"
    assert not r.get("force_ship")
    print("  ✅ A6: C reject 单轮 → revise(对等任一否决)")


def test_a7_both_pass_ship():
    """B ship + C ship → ship(双过)"""
    rounds = [{"round": 1, "b_verdict": "ship", "c_verdict": "sign",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship"
    assert not r.get("force_ship"), "正常双过不该 force_ship"
    print("  ✅ A7: B+C 双过 → ship")


def test_a8_b_skip_c_ship_ship():
    """B skip + C ship → 听 C(ship)→ ship + degraded"""
    rounds = [{"round": 1, "b_verdict": "skip", "c_verdict": "sign",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship"
    print("  ✅ A8: B skip + C ship → 听 C ship")


def test_a9_b_ship_c_skip_ship():
    """B ship + C skip → 听 B(ship)→ ship + degraded"""
    rounds = [{"round": 1, "b_verdict": "ship", "c_verdict": "skip",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship"
    print("  ✅ A9: B ship + C skip → 听 B ship")


def _write_r18p0_lint(name):
    """helper:写一个含 R18-P0 的 lint json,返回路径"""
    import json as _json
    import tempfile
    from pathlib import Path as _P
    tmp = _P(tempfile.mkdtemp())
    lint_p = tmp / name
    lint_p.write_text(_json.dumps({
        "violations": [{"rule_id": "R18_P0_self_as_ai", "issue": "自指 AI", "matches": []}]
    }), encoding="utf-8")
    return str(lint_p)


def test_a10_r18_p0_at_ceiling_aborts(tmp_path=None):
    """末轮 R18-P0 + 到天花板 → aborted_r18(自动终止,不 ship,无人工)"""
    lint_p = _write_r18p0_lint("v3.lint.json")
    rounds = [
        {"round": 1, "b_verdict": "no-ship", "c_verdict": "no-sign",
         "draft_path": "d1.md", "lint_json_path": None},
        {"round": 2, "b_verdict": "no-ship", "c_verdict": "no-sign",
         "draft_path": "d2.md", "lint_json_path": None},
        {"round": 3, "b_verdict": "ship", "c_verdict": "sign",
         "draft_path": "d3.md", "lint_json_path": lint_p},
    ]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "aborted_r18", \
        f"末轮 R18-P0 到天花板应 aborted_r18,实际 {r['decision']}"
    assert not r.get("force_ship"), "R18-P0 时绝不能 force_ship(即使 B+C 双过)"
    print("  ✅ A10: 末轮 R18-P0 + 天花板 → aborted_r18(自动终止,无人工)")


def test_a11_r18_p0_early_round_revise(tmp_path=None):
    """R18-P0 在未到天花板的轮次 → revise(自动修,不立即 abort,全流程无人工)"""
    lint_p = _write_r18p0_lint("v1.lint.json")
    rounds = [
        {"round": 1, "b_verdict": "ship", "c_verdict": "sign",
         "draft_path": "d1.md", "lint_json_path": lint_p},
    ]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "revise", \
        f"R18-P0 未到天花板应 revise 自动修,实际 {r['decision']}"
    assert r.get("r18_p0_in_last") is True
    assert not r.get("force_ship")
    print("  ✅ A11: R18-P0 早轮 → revise 自动修(给 writer 删段机会,无人工)")


def test_a12_r18_p0_fixed_then_ship(tmp_path=None):
    """早轮 R18-P0 但末轮已修掉 → 正常双轨 gate(不因历史 P0 误杀)"""
    lint_p = _write_r18p0_lint("v0.lint.json")
    rounds = [
        {"round": 1, "b_verdict": "no-ship", "c_verdict": "ship",
         "draft_path": "d0.md", "lint_json_path": lint_p},
        {"round": 2, "b_verdict": "ship", "c_verdict": "sign",
         "draft_path": "d1.md", "lint_json_path": None},  # 末轮无 P0
    ]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship", \
        f"末轮已修掉 R18-P0 应正常 ship,实际 {r['decision']}"
    print("  ✅ A12: 早轮 P0 末轮已修 → 正常 ship(不因历史误杀)")


# ============================================================
# B. fix_punctuation
# ============================================================

def test_b1_paired_double_quotes():
    text, n = fix_punctuation.fix_punctuation_text('他说"你好"然后离开了')
    assert text == '他说“你好”然后离开了', f"got: {text}"
    assert n == 2, f"got: {n}"
    print("  ✅ B1: 配对双引号 → 中文 “”")


def test_b2_chinese_comma_period():
    text, n = fix_punctuation.fix_punctuation_text('我说,你听.这是简单的.')
    assert text == '我说，你听。这是简单的。', f"got: {text!r}"
    assert n == 3, f"got: {n}"
    print("  ✅ B2: 中文间 ,. → ，。")


def test_b3_chinese_question_exclaim():
    text, n = fix_punctuation.fix_punctuation_text('真的?不可能!')
    assert text == '真的？不可能！', f"got: {text!r}"
    assert n == 2, f"got: {n}"
    print("  ✅ B3: 中文间 ?! → ?!")


def test_b4_numbers_not_touched():
    """1.5 / 3.14 不应被改"""
    text, n = fix_punctuation.fix_punctuation_text('价格 1.5 万元,数据 3.14')
    # 中文+逗号+空格+数字应该改逗号为, 但1.5和3.14不动
    assert "1.5" in text, f"1.5 被改: {text}"
    assert "3.14" in text, f"3.14 被改: {text}"
    print("  ✅ B4: 1.5 / 3.14 不动")


def test_b5_english_not_touched():
    """English, only. 不应被改"""
    text, _ = fix_punctuation.fix_punctuation_text('English, only.')
    assert text == 'English, only.', f"英文被改: {text}"
    print("  ✅ B5: 纯英文标点不动")


def test_b6_fenced_code_skipped():
    """fenced 代码块不应被改(全文件级测试)"""
    src = '''---
title: test
---

中文正文,带半角逗号.

```python
x = "hello"  # 这里的引号不动
y = 1,2,3    # 逗号不动
```

继续正文,再来一个.'''
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(src)
        path = Path(f.name)
    try:
        total, skipped = fix_punctuation.fix_punctuation_file(path)
        result = path.read_text(encoding="utf-8")
        assert 'x = "hello"' in result, f"代码块引号被改: {result}"
        assert 'y = 1,2,3' in result, f"代码块逗号被改: {result}"
        assert '中文正文，带半角逗号。' in result, f"正文未改: {result!r}"
        assert '继续正文，再来一个。' in result, f"正文未改: {result!r}"
        assert skipped >= 1, f"应跳过至少 1 个代码块,实际 {skipped}"
        print(f"  ✅ B6: fenced code 跳过(total={total}, skipped={skipped})")
    finally:
        path.unlink()


# ============================================================
# 主入口
# ============================================================

def run_all():
    tests = [
        ("A. critic_vote W2.C6 双轨全自动 + 隐藏天花板", [
            test_a1_b_reject_single_round_goes_revise,
            test_a2_b_reject_three_rounds_force_ship,
            test_a3_c_reject_three_rounds_force_ship,
            test_a4_double_skip_revise_not_abort,
            test_a5_double_skip_three_rounds_force_ship,
            test_a6_c_reject_single_round_revise,
            test_a7_both_pass_ship,
            test_a8_b_skip_c_ship_ship,
            test_a9_b_ship_c_skip_ship,
            test_a10_r18_p0_at_ceiling_aborts,
            test_a11_r18_p0_early_round_revise,
            test_a12_r18_p0_fixed_then_ship,
        ]),
        ("B. fix_punctuation 重建", [
            test_b1_paired_double_quotes,
            test_b2_chinese_comma_period,
            test_b3_chinese_question_exclaim,
            test_b4_numbers_not_touched,
            test_b5_english_not_touched,
            test_b6_fenced_code_skipped,
        ]),
    ]

    passed = 0
    failed = 0
    fail_msgs: list[str] = []

    for group_name, group_tests in tests:
        print(f"\n=== {group_name} ===")
        for t in group_tests:
            try:
                t()
                passed += 1
            except AssertionError as e:
                failed += 1
                msg = f"  ❌ {t.__name__}: {e}"
                print(msg)
                fail_msgs.append(msg)
            except Exception as e:
                failed += 1
                msg = f"  💥 {t.__name__} 异常: {type(e).__name__}: {e}"
                print(msg)
                fail_msgs.append(msg)

    print(f"\n{'='*60}")
    print(f"Round 26 fixes test: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    if failed:
        print("\n失败汇总:")
        for m in fail_msgs:
            print(m)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
