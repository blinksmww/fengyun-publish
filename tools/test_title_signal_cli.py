"""
test_title_signal_cli.py — title_signal CLI + W9 维度重校单测

W6: I/O 层(--title/--topic-keywords/--body-chars/--draft → score_title → JSON)。
W9: 砍致命组合 risk 检测(B4 0/321)+ 7钩子 hard gate→软分 + 4特质 ≥2→≥1。
    tb_ratio/english_chars 留作 advisory 报告项(PHASE1 ρ-0.32,只砍坏掉的 risk 门)。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

from title_signal import main, score_title, _count_chars  # noqa: E402

_TITLE = "别再用提示词去 AI 味了,方向就是错的"


def test_main_title_explicit(tmp_path, capsys):
    rc = main(["--title", _TITLE, "--topic-keywords", "AI", "Anthropic", "--body-chars", "4000"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "verdict" in out and "hook_type" in out and "score_total" in out


def test_cli_matches_function(tmp_path, capsys):
    """CLI JSON 必须 == 直接调 score_title(I/O-only 证据)."""
    main(["--title", _TITLE, "--topic-keywords", "AI", "--body-chars", "4000"])
    via_cli = json.loads(capsys.readouterr().out)
    via_fn = score_title(_TITLE, topic_keywords=["AI"], body_chars=4000)
    assert via_cli == via_fn


def test_main_draft_extracts_title_and_bodychars(tmp_path, capsys):
    """--draft:从 frontmatter 抽 title + 用正文算 body_chars."""
    body = "正文第一段。" * 80
    draft = tmp_path / "20260527-test-v0.md"
    draft.write_text(
        f"---\ntitle: {_TITLE}\nauthor: 研究Agent的云\n---\n\n{body}\n",
        encoding="utf-8",
    )
    rc = main(["--draft", str(draft), "--topic-keywords", "AI"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    # 抽出的 title 应等于 frontmatter 里的 title → 跟显式调一致
    expected = score_title(_TITLE, topic_keywords=["AI"], body_chars=_count_chars("\n\n" + body + "\n"))
    assert out["char_count"] == expected["char_count"]
    assert out["hook_type"] == expected["hook_type"]
    assert out["tb_ratio"] == expected["tb_ratio"]


def test_main_default_body_chars(capsys):
    """不给 --body-chars 也不给 --draft → score_title 用默认 5000."""
    rc = main(["--title", _TITLE])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out == score_title(_TITLE)


def test_seven_hook_no_longer_hard_gate():
    """W9: 7钩子 hard gate → 软分。无钩子但其它维高分(70≥65)应 pass(旧版强制 redo)。"""
    r = score_title("Claude 让我重新爱上了写东西这件小事", topic_keywords=["Claude"])
    assert r["hook_type"] is None
    assert r["score_total"] >= 65
    assert r["verdict"] == "pass"


def test_weak_title_still_redo():
    """软分门槛仍拦真弱标题:无钩子 + 低分(50<65) → redo。"""
    r = score_title("我的小尝试", topic_keywords=["AI"])
    assert r["verdict"] == "redo"


def test_fatal_combo_risk_removed():
    """W9: 砍致命组合 risk(B4 0/321);tb_ratio/english_chars 留 advisory(PHASE1 ρ-0.32)。"""
    r = score_title("我的小尝试", topic_keywords=["AI"])
    assert "fatal_combo_risk" not in r
    assert "tb_ratio" in r and "english_chars" in r


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
