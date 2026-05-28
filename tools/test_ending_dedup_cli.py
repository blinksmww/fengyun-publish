"""
test_ending_dedup_cli.py — W6 C6 ending_dedup argparse CLI 单测

只测 I/O 层(--draft 读全文 → check_ending_overlap,draft 同时作 current_draft_path)。
去重算法(extract_ending/tokenize/jaccard/5-gram/阈值)W6 一行未改。
未碰 opening_dedup 基础库导出。fixture 用乱码末段保证确定性。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

from ending_dedup import main, check_ending_overlap  # noqa: E402

_ARTICLE = """---
title: 测试稿乱码
author: 研究Agent的云
---

## 正文

zqxjk wbplm vntru 正文内容甲乙丙。

## 收束

fkdls mqpwx yqwer ziopl 末段乱码内容,绝不跟真 drafts 撞型,hgvbn jrtke cwluo。
asdfg hjklp zxcvb nmqwe 继续乱码保证 token 不重叠,rtyui opasd fghjk lzxcv。
"""


def test_main_draft(tmp_path, capsys):
    draft = tmp_path / "20260527-test-v0.md"
    draft.write_text(_ARTICLE, encoding="utf-8")
    rc = main(["--draft", str(draft), "--max-age-days", "30", "--max-n-check", "5"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "is_too_similar" in out and "max_jaccard" in out and "max_ngram_overlap" in out


def test_cli_matches_function(tmp_path, capsys):
    """CLI JSON 必须 == 直接调 check_ending_overlap(draft 作 current_draft_path)."""
    draft = tmp_path / "20260527-test-v0.md"
    draft.write_text(_ARTICLE, encoding="utf-8")
    main(["--draft", str(draft), "--max-age-days", "30", "--max-n-check", "5"])
    via_cli = json.loads(capsys.readouterr().out)
    via_fn = check_ending_overlap(
        draft.read_text(encoding="utf-8"),
        max_age_days=30, max_n_check=5,
        current_draft_path=draft,
    )
    assert via_cli == via_fn


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
