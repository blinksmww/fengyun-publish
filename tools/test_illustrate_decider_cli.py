"""
test_illustrate_decider_cli.py — W6 C9 illustrate_decider argparse CLI 单测

只测 I/O / 路由层:
- dry(默认 + --dry-run + 位置参数向后兼容)→ read_article_meta + pick_candidates
- --generate --decision → 到达 generate_from_decision + write_metadata 分支
  (实 Seedream API 不 unit 测,用 monkeypatch 拦截,只断言 argparse 路由 + 参数透传)
出图/写 metadata 业务逻辑 W6 一行未改。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

import illustrate_decider as ild  # noqa: E402
from illustrate_decider import main  # noqa: E402

_DRAFT = """---
title: 测试稿
slug: test-slug-w6
author: 研究Agent的云
---

开场段落,这里是 intro 内容,足够长以便预筛能识别候选位置,继续凑字数到八十以上确保达到阈值的样子。

## 第一章

这是第一章正文,内容也要足够长,凑够字数让 pick_candidates 把它当作候选位置之一,继续写到八十字符以上。
"""


def _make_draft(tmp_path: Path) -> Path:
    d = tmp_path / "20260527-test-v0.md"
    d.write_text(_DRAFT, encoding="utf-8")
    return d


def test_dry_default_positional(tmp_path, capsys):
    """位置参数 + 无 flag → 默认 dry(向后兼容 Step 7.1)."""
    draft = _make_draft(tmp_path)
    rc = main([str(draft)])
    assert rc == 0
    assert "Article meta" in capsys.readouterr().out


def test_dry_flag(tmp_path, capsys):
    """--draft + --dry-run → dry."""
    draft = _make_draft(tmp_path)
    rc = main(["--draft", str(draft), "--dry-run"])
    assert rc == 0
    assert "候选位置" in capsys.readouterr().out


def test_generate_branch_reached(tmp_path, monkeypatch, capsys):
    """--generate --decision:argparse 路由到 generate_from_decision + write_metadata,参数透传正确."""
    draft = _make_draft(tmp_path)
    decision = {
        "should_illustrate": True, "count": 1, "prompts": ["a warm sketch"],
        "image_at_h2_indices": [0], "style_anchor": "warm sketchnote",
        "alts": ["示意图"], "positions": [{"h2_title": "第一章"}],
    }
    dj = tmp_path / "image_decision.json"
    dj.write_text(json.dumps(decision, ensure_ascii=False), encoding="utf-8")

    calls: dict = {}

    def fake_generate(dec, output_dir, slug, max_workers=3, retry_failed=True):
        calls["gen"] = dict(dec=dec, output_dir=output_dir, slug=slug,
                            max_workers=max_workers, retry_failed=retry_failed)
        return [Path("output/images/test-slug-w6-01.png")]

    def fake_write(draft_path, dec, image_paths):
        calls["write"] = dict(draft_path=draft_path, dec=dec, image_paths=image_paths)

    monkeypatch.setattr(ild, "generate_from_decision", fake_generate)
    monkeypatch.setattr(ild, "write_metadata", fake_write)

    rc = main(["--draft", str(draft), "--generate", "--decision", str(dj), "--slug", "test-slug-w6"])
    assert rc == 0
    assert "gen" in calls and "write" in calls
    assert calls["gen"]["slug"] == "test-slug-w6"
    assert calls["gen"]["max_workers"] == 3 and calls["gen"]["retry_failed"] is True
    assert calls["gen"]["output_dir"] == ild.OUT_DIR
    assert calls["gen"]["dec"]["should_illustrate"] is True
    # stdout 是 image_paths 的 JSON list
    printed = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert isinstance(printed, list) and printed


def test_generate_slug_defaults_from_meta(tmp_path, monkeypatch, capsys):
    """--generate 不给 --slug → 从 read_article_meta 推断(frontmatter slug)."""
    draft = _make_draft(tmp_path)
    dj = tmp_path / "image_decision.json"
    dj.write_text(json.dumps({"should_illustrate": True, "prompts": ["x"]}, ensure_ascii=False),
                  encoding="utf-8")
    calls: dict = {}
    monkeypatch.setattr(ild, "generate_from_decision",
                        lambda dec, output_dir, slug, **kw: calls.setdefault("slug", slug) or [Path("output/images/a-01.png")])
    monkeypatch.setattr(ild, "write_metadata", lambda *a, **k: None)
    rc = main(["--draft", str(draft), "--generate", "--decision", str(dj)])
    assert rc == 0
    assert calls["slug"] == "test-slug-w6"  # frontmatter slug


def test_generate_requires_decision(tmp_path):
    """--generate 缺 --decision → argparse error(SystemExit)."""
    draft = _make_draft(tmp_path)
    with pytest.raises(SystemExit):
        main(["--draft", str(draft), "--generate"])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
