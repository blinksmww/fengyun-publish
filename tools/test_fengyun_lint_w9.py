"""
test_fengyun_lint_w9.py — W9 清伪 lint + 修 R7 词典 单测

W9 (lint-vs-founder-split 铁律):砍 6 条「灵魂判断伪装成机械规则」(无源 + 品味 + 已被 B/C/王小波覆盖):
  R2_bizhe_overload / R4_dash_stack / R13_insufficient_anxiety_buildup /
  R14_premature_consolation / R16_dangling_ending / R21_bold_ai_padding
机械核(R0/R18/R29/R30/R19/R5...)+ huashu 块不动。
R7 修词典:删歧义词(强调/证明/增强/凸显/格局,正常中文 → 误判率>0)只留真 AI 味词。
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

import fengyun_lint  # noqa: E402

CUT_RULE_IDS = {
    "R2_bizhe_overload",
    "R4_dash_stack",
    "R13_insufficient_anxiety_buildup",
    "R14_premature_consolation",
    "R16_dangling_ending",
    "R21_bold_ai_padding",
}


def _build_cut_fixture(tmp_path: Path) -> Path:
    """构造一篇曾经会触发全部 6 条被砍规则的 AI 深度文(>2000 字)."""
    body = "# 关于 Claude 和 Agent 的深度思考\n\n"
    body += "泡杯茶,我们慢慢聊。笔者认为这件事——其实很——重要。笔者再说一句。笔者第三次。\n\n"
    body += "笔者笔者笔者笔者笔者笔者笔者继续展开。\n\n"
    for i in range(60):
        body += f"这是第{i}段正文,讲 AI agent 的能力边界和工程实践,展开来说有不少细节值得推敲琢磨一番。\n\n"
    body += " ".join(f"**词{i}**" for i in range(12)) + "\n\n"
    body += "完。\n"
    fm = "---\ntitle: Claude Agent 深度思考\ntopic_type: ai\n---\n\n"
    p = tmp_path / "w9_cut_fixture.md"
    p.write_text(fm + body, encoding="utf-8")
    return p


def _rule_ids(res: dict) -> set[str]:
    return {(v["rule_id"] if isinstance(v, dict) else v.rule_id) for v in res["violations"]}


def test_w9_cut_rules_absent(tmp_path):
    """W9 砍的 6 条规则:在曾触发它们的 fixture 上不再出现."""
    res = fengyun_lint.lint_article(_build_cut_fixture(tmp_path))
    leaked = CUT_RULE_IDS & _rule_ids(res)
    assert not leaked, f"W9 应砍的伪 lint 规则仍触发: {sorted(leaked)}"


def test_w9_kept_mechanical_core_still_fires(tmp_path):
    """守护:机械核没被误删 —— 同 fixture(2905 字 <4000)仍触发 R12 字数规则."""
    res = fengyun_lint.lint_article(_build_cut_fixture(tmp_path))
    ids = _rule_ids(res)
    assert "R12_word_count_too_short" in ids, "机械核 R12 不应被 W9 误删"


def _lint_text(tmp_path: Path, text: str) -> set[str]:
    p = tmp_path / "r7_probe.md"
    p.write_text("---\ntitle: t\n---\n\n" + text + "\n", encoding="utf-8")
    return _rule_ids(fengyun_lint.lint_article(p))


def test_r7_drops_ambiguous_normal_chinese(tmp_path):
    """W9 修 R7:删歧义词 —— 强调/证明/增强/凸显/格局 是正常中文,不该再触发 R7(误判率→0)."""
    ids = _lint_text(tmp_path, "他强调要证明这个方案,增强信心,凸显格局。")
    assert "R7_ai_writing_markers" not in ids, "R7 不应被正常中文词误触发"


def test_r7_keeps_real_ai_markers(tmp_path):
    """W9 修 R7:真 AI 味词保留 —— 此外/至关重要 仍触发 R7."""
    ids = _lint_text(tmp_path, "此外,这个方案至关重要,值得深入探讨。")
    assert "R7_ai_writing_markers" in ids, "R7 应仍抓真 AI 味词"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
