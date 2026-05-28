"""
test_event_dedup_cli.py — W6 C2 event_dedup argparse CLI 单测

只测 I/O 层(读 ranked.json → 逐条 check_event_dedup → chosen + filtered → 写 JSON)。
去重算法(event_fingerprint / jaccard / containment / 阈值 0.40)W6 一行未改。

为保证确定性,fixture 用绝不会跟真 drafts/runs 命中的乱码标题
(check_event_dedup 扫真实 output/drafts + output/runs,乱码 → 全部 is_duplicate=False)。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

from event_dedup import main, check_event_dedup  # noqa: E402

# 乱码 token,保证跟任何真 draft/run 的事件指纹 Jaccard ≈ 0
_UNIQ = [
    {"title": "zqxjk7 wbplm3 事件甲 vntru9", "summary": "fkdls2 mqpwx"},
    {"title": "hgvbn4 jrtke8 事件乙 cwluo1", "summary": "psdmz6 tklne"},
    {"title": "yqwer5 ziopl0 事件丙 mnbvc2", "summary": "asdfg9 hjklp"},
]


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def test_main_chosen_and_filtered(tmp_path, capsys):
    ranked = tmp_path / "ranked.json"
    out = tmp_path / "chosen.json"
    _write_json(ranked, _UNIQ)

    rc = main(["--in", str(ranked), "--days", "7", "--out", str(out)])
    assert rc == 0

    assert out.exists()
    res = json.loads(out.read_text(encoding="utf-8"))
    # 乱码标题不撞型 → 全部进 filtered,chosen = 第一个
    assert res["n_in"] == 3
    assert res["n_filtered"] == 3
    assert res["chosen"]["title"] == _UNIQ[0]["title"]
    assert [it["title"] for it in res["filtered"]] == [it["title"] for it in _UNIQ]

    printed = json.loads(capsys.readouterr().out)
    assert printed["chosen"]["title"] == _UNIQ[0]["title"]


def test_main_empty_input(tmp_path):
    ranked = tmp_path / "ranked.json"
    _write_json(ranked, [])
    rc = main(["--in", str(ranked)])
    assert rc == 0


def test_main_accepts_current_draft_and_no_published(tmp_path):
    """--current-draft 与 --no-include-published 被接受且不崩."""
    ranked = tmp_path / "ranked.json"
    _write_json(ranked, _UNIQ)
    rc = main([
        "--in", str(ranked),
        "--current-draft", str(tmp_path / "self-v0.md"),
        "--no-include-published",
    ])
    assert rc == 0


def test_cli_filtered_matches_function(tmp_path):
    """CLI 的 filtered 必须 == 直接逐条调 check_event_dedup 的过滤结果(I/O-only 证据)."""
    ranked = tmp_path / "ranked.json"
    out = tmp_path / "chosen.json"
    _write_json(ranked, _UNIQ)
    main(["--in", str(ranked), "--days", "7", "--out", str(out)])
    via_cli = json.loads(out.read_text(encoding="utf-8"))["filtered"]
    via_fn = [it for it in _UNIQ
              if not check_event_dedup(it, days=7, include_published=True)["is_duplicate"]]
    assert [it["title"] for it in via_cli] == [it["title"] for it in via_fn]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
