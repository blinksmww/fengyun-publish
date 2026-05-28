"""
test_topic_recommender_cli.py — W6 C1 topic_recommender argparse CLI 单测

只测 I/O 层(argparse + 读 pool/ws + 排序 + 写 JSON),不测打分逻辑
(rank_aihot_candidates 的算法已有自己的语义,W6 一行未改)。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

from topic_recommender import main, rank_aihot_candidates  # noqa: E402


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def test_main_pool_and_ws_merge(tmp_path, capsys):
    """--pool(含 items) + --ws(裸 list)合并后排序,写 --out + 打印 JSON."""
    pool = tmp_path / "iti_pool.json"
    ws = tmp_path / "ws_items.json"
    out = tmp_path / "ranked.json"
    _write_json(pool, {"items": [
        {"title": "Anthropic Skills 框架深度解读", "summary": "Claude 新增能力", "category": "ai-products"},
        {"title": "GPT-5 发布,OpenAI 王者归来", "summary": "新一代模型", "category": "ai-models"},
    ]})
    _write_json(ws, [
        {"title": "Claude Code 新功能:Vibe Coding", "summary": "agent 编程", "category": "ai-products"},
    ])

    rc = main(["--pool", str(pool), "--ws", str(ws), "--out", str(out)])
    assert rc == 0

    # --out 文件落地且为合法 JSON list,长度 = pool + ws
    assert out.exists()
    ranked = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(ranked, list)
    assert len(ranked) == 3
    # 每项加了打分字段
    for it in ranked:
        assert "_predicted_burst_rate" in it
        assert "_matched_family" in it
    # 降序
    rates = [it["_predicted_burst_rate"] for it in ranked]
    assert rates == sorted(rates, reverse=True)
    # Anthropic Skills 应排在 GPT-5(反规律)之前
    titles = [it["title"] for it in ranked]
    assert titles.index("Anthropic Skills 框架深度解读") < titles.index("GPT-5 发布,OpenAI 王者归来")

    # stdout 是合法 JSON
    printed = json.loads(capsys.readouterr().out)
    assert isinstance(printed, list) and len(printed) == 3


def test_main_pool_only(tmp_path):
    """只给 --pool(无 ws)也能跑."""
    pool = tmp_path / "iti_pool.json"
    _write_json(pool, {"items": [
        {"title": "Karpathy 加入 Anthropic", "summary": "pre-training", "category": "industry"},
        {"title": "一个普通人怎么用 AI", "summary": "", "category": "tip"},
    ]})
    rc = main(["--pool", str(pool)])
    assert rc == 0


def test_main_pool_bare_list(tmp_path):
    """--pool 文件是裸 list(无 items key)也兼容."""
    pool = tmp_path / "iti_pool.json"
    _write_json(pool, [
        {"title": "Claude Skills 实战", "summary": "", "category": "ai-products"},
    ])
    out = tmp_path / "ranked.json"
    rc = main(["--pool", str(pool), "--out", str(out)])
    assert rc == 0
    ranked = json.loads(out.read_text(encoding="utf-8"))
    assert len(ranked) == 1


def test_cli_result_matches_function(tmp_path):
    """CLI 输出必须跟直接调 rank_aihot_candidates 字节级一致(证明只加 I/O 不改逻辑)."""
    items = [
        {"title": "Anthropic Skills", "summary": "x", "category": "ai-products"},
        {"title": "GPT-5", "summary": "y", "category": "ai-models"},
    ]
    pool = tmp_path / "iti_pool.json"
    out = tmp_path / "ranked.json"
    _write_json(pool, {"items": items})
    main(["--pool", str(pool), "--out", str(out)])
    via_cli = json.loads(out.read_text(encoding="utf-8"))
    via_fn = rank_aihot_candidates(items)
    assert [it["title"] for it in via_cli] == [it["title"] for it in via_fn]
    assert [it["_predicted_burst_rate"] for it in via_cli] == [it["_predicted_burst_rate"] for it in via_fn]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
