"""
test_ending_signal_cli.py — W6 C5 ending_signal argparse CLI 单测

只测 I/O 层(--draft 读全文 → score_ending_signal → JSON)。
4 维评分 + 物理约束(末段字数/金句/摘要/召唤/阈值)W6 一行未改。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

from ending_signal import main, score_ending_signal  # noqa: E402

_ARTICLE = """---
title: 测试稿
author: 研究Agent的云
---

## 正文

一些正文内容。

## 收束

说到底,这件事没有标准答案。不是技术变了,而是我们看世界的方式变了。

愿你也能在这场变化里,为自己立一颗小小的心。共勉。
"""


def test_main_draft(tmp_path, capsys):
    draft = tmp_path / "20260527-test-v0.md"
    draft.write_text(_ARTICLE, encoding="utf-8")
    rc = main(["--draft", str(draft)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "verdict" in out and "physical_pass" in out and "last_section_chars" in out


def test_cli_matches_function(tmp_path, capsys):
    """CLI JSON 必须 == 直接调 score_ending_signal(读同一文件全文)."""
    draft = tmp_path / "20260527-test-v0.md"
    draft.write_text(_ARTICLE, encoding="utf-8")
    main(["--draft", str(draft)])
    via_cli = json.loads(capsys.readouterr().out)
    via_fn = score_ending_signal(draft.read_text(encoding="utf-8"))
    assert via_cli == via_fn


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
