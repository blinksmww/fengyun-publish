"""
test_title_dedup_cli.py — W6 C4 title_dedup argparse CLI 单测

只测 I/O 层(--title/--hook-type/--draft/--max-age-days/--max-n-check → check_title_overlap → JSON)。
去重算法(tokenize/jaccard/5-gram/钩子撞型/阈值)W6 一行未改。
--draft → current_draft_path(Bug 4 防 self-match)。

fixture 用乱码标题保证跟真 drafts 不撞型(确定性)。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

from title_dedup import main, check_title_overlap  # noqa: E402

_NONSENSE = "zqxjk7 wbplm3 标题甲 vntru9 fkdls2 mqpwx 不会撞型"


def test_main_title_explicit(capsys):
    rc = main(["--title", _NONSENSE, "--hook-type", "颠覆认知",
               "--max-age-days", "14", "--max-n-check", "10"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "is_too_similar" in out and "max_jaccard" in out and "hook_clash" in out


def test_cli_matches_function(capsys):
    """CLI JSON 必须 == 直接调 check_title_overlap(I/O-only 证据)."""
    main(["--title", _NONSENSE, "--hook-type", "颠覆认知",
          "--max-age-days", "14", "--max-n-check", "10"])
    via_cli = json.loads(capsys.readouterr().out)
    via_fn = check_title_overlap(_NONSENSE, hook_type="颠覆认知",
                                 max_age_days=14, max_n_check=10)
    assert via_cli == via_fn


def test_main_draft_supplies_title_and_self_exclude(tmp_path, capsys):
    """--draft:无 --title 时从 frontmatter 抽 title,且作 current_draft_path(防 self-match)."""
    draft = tmp_path / "20260527-test-v0.md"
    draft.write_text(
        f"---\ntitle: {_NONSENSE}\nauthor: 研究Agent的云\n---\n\n正文。\n",
        encoding="utf-8",
    )
    rc = main(["--draft", str(draft), "--max-age-days", "14", "--max-n-check", "10"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    via_fn = check_title_overlap(_NONSENSE, hook_type=None,
                                 max_age_days=14, max_n_check=10,
                                 current_draft_path=draft)
    assert out == via_fn


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
