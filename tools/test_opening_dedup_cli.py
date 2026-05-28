"""
test_opening_dedup_cli.py — W6 C8 opening_dedup argparse CLI 单测

只测 I/O 层(--trial 直读 / --draft 抽 intro → check_opening_overlap;--current-draft 防 self-match)。
去重算法 + base 库导出(tokenize/char_5grams/jaccard/overlap_ratio/阈值)W6 一行未改。
fixture 用乱码开头保证跟真 drafts 不撞型(确定性)。
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

from opening_dedup import main, check_opening_overlap  # noqa: E402

_OPENING = (
    "zqxjk wbplm vntru,fkdls mqpwx yqwer ziopl 这是绝不会撞型的乱码开头,"
    "hgvbn jrtke cwluo asdfg hjklp 继续保证 token 不重叠。"
)


def test_main_trial(tmp_path, capsys):
    trial = tmp_path / "opening_trial.txt"
    trial.write_text(_OPENING, encoding="utf-8")
    rc = main(["--trial", str(trial)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "is_too_similar" in out and "max_jaccard" in out and "max_ngram_overlap" in out


def test_cli_trial_matches_function(tmp_path, capsys):
    trial = tmp_path / "opening_trial.txt"
    trial.write_text(_OPENING, encoding="utf-8")
    main(["--trial", str(trial)])
    via_cli = json.loads(capsys.readouterr().out)
    via_fn = check_opening_overlap(trial.read_text(encoding="utf-8"),
                                   max_age_days=30, max_n_check=5)
    assert via_cli == via_fn


def test_main_draft_intro_and_self_exclude(tmp_path, capsys):
    """--draft:抽 intro + 默认自身作 current_draft_path."""
    draft = tmp_path / "20260527-test-v0.md"
    draft.write_text(
        f"---\ntitle: 乱码\n---\n\n{_OPENING}\n\n## 正文\n\n正文。\n",
        encoding="utf-8",
    )
    rc = main(["--draft", str(draft)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)

    raw = draft.read_text(encoding="utf-8")
    body = raw.split("---", 2)[2]
    m = re.search(r"\n##\s", body)
    intro = (body[:m.start()] if m else body).strip()
    via_fn = check_opening_overlap(intro, max_age_days=30, max_n_check=5,
                                   current_draft_path=draft)
    assert out == via_fn


def test_main_trial_with_current_draft(tmp_path, capsys):
    """--trial + --current-draft:显式排除某 draft(Step 6.5 形态)."""
    trial = tmp_path / "opening_trial.txt"
    trial.write_text(_OPENING, encoding="utf-8")
    rc = main(["--trial", str(trial), "--current-draft", str(tmp_path / "self-v0.md")])
    assert rc == 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
