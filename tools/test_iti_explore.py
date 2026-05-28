"""
test_iti_explore.py — ITI I-2 深搜单测

重点测 Round 27 新增的 fetch_trendradar_topic():
- 主题命中过滤
- 空 entities 降级
- 完全无匹配
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# 让 import 找到 tools/
ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

import iti_explore  # noqa: E402  (module 句柄,给 monkeypatch 用)
from iti_explore import fetch_trendradar_topic, cli, merge_with_websearch  # noqa: E402


# ============================================================
# fetch_trendradar_topic
# ============================================================

def test_fetch_trendradar_topic_with_entities():
    """主题命中过滤 — 用常见的 AI 实体词,应该至少匹配若干条."""
    items = fetch_trendradar_topic(
        ["Anthropic", "Claude", "AI", "OpenAI", "Google"],
        top_k=20,
    )
    # 当 TrendRadar 数据活的时候,这些 AI 大词应该至少命中 1 条
    # 如果 TrendRadar 文件过期或不存在,返回 [] 也是合法行为(降级)
    assert isinstance(items, list)
    if items:
        # 命中条目必须有 title/url 字段
        for it in items:
            assert "title" in it
            assert "url" in it
            assert it.get("_origin") == "trendradar"


def test_fetch_trendradar_topic_empty_entities():
    """传 [] 应该走降级返回前 top_k 条."""
    items = fetch_trendradar_topic([], top_k=5)
    assert isinstance(items, list)
    # 文件活的话至少有几条;过期则 []
    assert len(items) <= 5


def test_fetch_trendradar_topic_no_match():
    """传不可能命中的随机词,应该返回 []."""
    items = fetch_trendradar_topic(
        ["zzzzzz_no_such_entity_should_match_xyz_12345"],
        top_k=10,
    )
    assert items == []


def test_fetch_trendradar_topic_top_k_cap():
    """top_k 截断生效."""
    items = fetch_trendradar_topic(["AI", "模型"], top_k=3)
    assert isinstance(items, list)
    assert len(items) <= 3


def test_fetch_trendradar_topic_case_insensitive():
    """大小写不敏感 — 全小写 entity 应该匹配大小写混合的 title."""
    upper_items = fetch_trendradar_topic(["ANTHROPIC"], top_k=20)
    lower_items = fetch_trendradar_topic(["anthropic"], top_k=20)
    # 大小写不敏感,两次结果应该一致
    assert len(upper_items) == len(lower_items)


def test_fetch_trendradar_topic_filters_empty_entity_strings():
    """entities 里混入空字符串不应该影响过滤."""
    items = fetch_trendradar_topic(["AI", "", None], top_k=10)  # type: ignore
    assert isinstance(items, list)


# ============================================================
# explore_topic 接入(快速 smoke,trendradar 在 sources 列表里)
# ============================================================

def test_explore_topic_includes_trendradar_in_stats():
    """explore_topic 的 stats 里必须有 trendradar key."""
    from iti_explore import explore_topic
    result = explore_topic(
        slug="test-trendradar-smoke",
        title="测试 TrendRadar 接入",
        entities=["zzzz_impossible_entity_xyz"],  # 故意不命中,跑得快
        main_source_urls=None,
        verbose=False,
    )
    assert "stats" in result
    assert "trendradar" in result["stats"], (
        f"explore_topic.stats 必须含 trendradar key,实际: {list(result['stats'].keys())}"
    )


def test_explore_topic_includes_aihot_query_in_stats(monkeypatch):
    """W8 E3a:explore_topic 的 stats 必须含 aihot-query key,facts 含其条目."""
    from iti_explore import explore_topic
    sentinel = [{"title": "AIHOT-Q-HIT", "url": "https://aihot/q/1",
                 "summary": "s", "source": "aihot:q:Anthropic", "_origin": "aihot"}]
    monkeypatch.setattr(iti_explore, "_fetch_aihot_by_query", lambda ents: sentinel)
    result = explore_topic(
        slug="test-aihot-query-smoke",
        title="测试 aihot ?q= 接入",
        entities=["zzzz_impossible_entity_xyz"],  # 其他源不命中,确保不早停
        main_source_urls=None,
        verbose=False,
    )
    assert "aihot-query" in result["stats"], (
        f"stats 必须含 aihot-query key,实际: {list(result['stats'].keys())}"
    )
    assert any(f.get("url") == "https://aihot/q/1" for f in result["facts"])


# ============================================================
# W6 C10: cli(argv) + --merge-ws / --out(只测 I/O 路由,explore 用 monkeypatch 拦)
# ============================================================

def test_cli_merge_ws_writes_facts(tmp_path, monkeypatch, capsys):
    """--merge-ws + --out:explore_topic 后 merge_with_websearch 并写 facts.json."""
    local = [
        {"title": "L1", "url": "http://a", "summary": "x"},
        {"title": "L2", "url": "http://b"},
    ]
    monkeypatch.setattr(
        iti_explore, "explore_topic",
        lambda *a, **k: {"facts": local, "stats": {}, "n_unique": len(local)},
    )
    ws = [
        {"title": "WS1", "url": "http://c", "summary": "y"},
        {"title": "WSdup", "url": "http://a"},   # 跟 local 撞 url,merge 去重
    ]
    ws_path = tmp_path / "ws_items_i2.json"
    ws_path.write_text(json.dumps(ws, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "facts.json"

    rc = cli(["test-slug", "测试标题", "--entities", "Anthropic", "OpenAI",
              "--merge-ws", str(ws_path), "--out", str(out)])
    assert rc == 0

    facts = json.loads(out.read_text(encoding="utf-8"))
    # CLI 输出必须 == 直接调 merge_with_websearch(I/O-only 证据;默认 max_total=25)
    expected = merge_with_websearch(local, ws, max_total=25)
    assert [f.get("url") for f in facts] == [f.get("url") for f in expected]


def test_cli_merge_ws_accepts_dict_items(tmp_path, monkeypatch):
    """--merge-ws 文件是 {items:[...]} 也兼容."""
    monkeypatch.setattr(
        iti_explore, "explore_topic",
        lambda *a, **k: {"facts": [], "stats": {}, "n_unique": 0},
    )
    ws_path = tmp_path / "ws.json"
    ws_path.write_text(json.dumps({"items": [{"title": "W", "url": "http://x"}]}, ensure_ascii=False),
                       encoding="utf-8")
    out = tmp_path / "facts.json"
    rc = cli(["s", "--merge-ws", str(ws_path), "--out", str(out)])
    assert rc == 0
    assert json.loads(out.read_text(encoding="utf-8"))[0]["url"] == "http://x"


def test_cli_explore_only_backward_compat(monkeypatch, capsys):
    """无 --merge-ws/--out → 原 explore 行为(向后兼容),返回 0."""
    monkeypatch.setattr(
        iti_explore, "explore_topic",
        lambda *a, **k: {"facts": [], "stats": {}, "n_unique": 0},
    )
    rc = cli(["test-slug", "--entities", "Anthropic"])
    assert rc == 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
