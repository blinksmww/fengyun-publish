"""
test_iti_collect_trendradar.py — W8 E2/E3a 单测

E2 TrendRadar DB reader(按 feed 取最新 N)+ markdown 回退 + 优先级
E3a fetch_aihot_by_query(?q= 实体搜索,全 mock 零真网络)

全部用 tmp sqlite / monkeypatch,**绝不触碰真 D:\\Dev\\TrendRadar**。
"""
from __future__ import annotations
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402,F401
import iti_collect  # noqa: E402  (module 句柄,给 monkeypatch 用)

# 只建本 wave 用到的两张表(真 schema 见 D:\Dev\TrendRadar\trendradar\storage\rss_schema.sql)
_RSS_SCHEMA = """
CREATE TABLE rss_feeds (id TEXT PRIMARY KEY, name TEXT);
CREATE TABLE rss_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL, feed_id TEXT NOT NULL, url TEXT NOT NULL,
    guid TEXT DEFAULT '', published_at TEXT, summary TEXT, author TEXT,
    first_crawl_time TEXT, last_crawl_time TEXT, crawl_count INTEGER DEFAULT 1
);
"""


def _make_db(path, feeds, items):
    con = sqlite3.connect(str(path))
    con.executescript(_RSS_SCHEMA)
    con.executemany("INSERT INTO rss_feeds(id,name) VALUES (?,?)", feeds)
    con.executemany(
        "INSERT INTO rss_items(title,feed_id,url,published_at,summary,"
        "first_crawl_time,last_crawl_time) VALUES (?,?,?,?,?,?,?)",
        items,
    )
    con.commit()
    con.close()


# ============================================================
# E2 — TrendRadar DB reader
# ============================================================

def test_db_reader_per_feed_n(tmp_path, monkeypatch):
    """2 feed × 4 item,per_feed_n=2 → 每 feed 取最新 2 条(按 published_at DESC)."""
    db = tmp_path / "2026-05-27.db"
    feeds = [("feedA", "Feed A"), ("feedB", "Feed B")]
    items = []
    for f in ("feedA", "feedB"):
        for d in range(1, 5):  # 4 条,published 2026-05-01..04
            items.append((f"{f}-title-{d}", f, f"https://x/{f}/{d}",
                          f"2026-05-0{d}T00:00:00Z", f"sum-{d}", "t", "t"))
    _make_db(db, feeds, items)
    monkeypatch.setattr(iti_collect, "TRENDRADAR_RSS_DIR", tmp_path)

    out = iti_collect._fetch_trendradar_db(per_feed_n=2)
    assert len(out) == 4  # 2 feed × 2

    titles = {o["title"] for o in out}
    assert "feedA-title-4" in titles and "feedA-title-3" in titles  # 最新两条
    assert "feedA-title-1" not in titles and "feedA-title-2" not in titles

    o = out[0]
    assert {"title", "summary", "url", "source",
            "category", "publishedAt", "_origin"}.issubset(o)
    assert o["_origin"] == "trendradar"
    assert o["source"].startswith("trendradar:")


def test_db_reader_no_db_returns_empty(tmp_path, monkeypatch):
    """空目录(无 *.db) → [](触发回退)."""
    monkeypatch.setattr(iti_collect, "TRENDRADAR_RSS_DIR", tmp_path)
    assert iti_collect._fetch_trendradar_db() == []


def test_db_reader_stale_returns_empty(tmp_path, monkeypatch):
    """DB mtime 过期(48h > 36h)→ [](触发回退)."""
    db = tmp_path / "2026-05-01.db"
    _make_db(db, [("f", "F")],
             [("t", "f", "https://x/1", "2026-05-01T00:00:00Z", "s", "t", "t")])
    old = time.time() - 48 * 3600
    os.utime(db, (old, old))
    monkeypatch.setattr(iti_collect, "TRENDRADAR_RSS_DIR", tmp_path)
    assert iti_collect._fetch_trendradar_db(max_age_hours=36) == []


def test_fetch_trendradar_prefers_db(tmp_path, monkeypatch):
    """DB 有数据 → fetch_trendradar 返 DB,不读 markdown."""
    db = tmp_path / "2026-05-27.db"
    _make_db(db, [("f", "F")],
             [("dbtitle", "f", "https://x/db", "2026-05-27T00:00:00Z", "s", "t", "t")])
    monkeypatch.setattr(iti_collect, "TRENDRADAR_RSS_DIR", tmp_path)
    monkeypatch.setattr(iti_collect, "TRENDRADAR_LATEST", tmp_path / "nope.md")  # 不存在
    out = iti_collect.fetch_trendradar()
    assert any(o["title"] == "dbtitle" for o in out)


def test_fetch_trendradar_falls_back_to_markdown(tmp_path, monkeypatch):
    """无 DB → 回退 markdown reader(原逻辑零改)."""
    monkeypatch.setattr(iti_collect, "TRENDRADAR_RSS_DIR", tmp_path)  # 空,无 .db
    md = tmp_path / "latest_daily.md"
    md.write_text("[新智元][某AI大新闻](https://example.com/news1)\n", encoding="utf-8")
    monkeypatch.setattr(iti_collect, "TRENDRADAR_LATEST", md)
    out = iti_collect.fetch_trendradar()
    assert len(out) == 1
    assert out[0]["url"] == "https://example.com/news1"
    assert out[0]["_origin"] == "trendradar"


# ============================================================
# E3a — aihot ?q= 关键词搜索(全 mock)
# ============================================================

class _FakeResp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_fetch_aihot_by_query_maps_and_dedups(monkeypatch):
    """逐 entity 调 ?q=,字段映射 + URL 去重."""
    calls = []

    def fake_urlopen(req, **kw):
        calls.append(req.full_url)
        if "Anthropic" in req.full_url:
            return _FakeResp({"items": [{"title": "A", "summary": "sa",
                                         "url": "https://u/1", "source": "x",
                                         "category": "c", "publishedAt": "p"}]})
        return _FakeResp({"items": [{"title": "B", "url": "https://u/1"}]})  # 同 url

    monkeypatch.setattr(iti_collect.urllib.request, "urlopen", fake_urlopen)
    out = iti_collect.fetch_aihot_by_query(["Anthropic", "Claude"])
    assert len(calls) == 2          # 逐 entity 各一次
    assert len(out) == 1            # url 去重
    assert out[0]["_origin"] == "aihot"
    assert out[0]["source"].startswith("aihot:q:")


def test_fetch_aihot_by_query_network_fail_continues(monkeypatch):
    """网络挂 → 不崩,返 []."""
    def boom(req, **kw):
        raise OSError("net down")

    monkeypatch.setattr(iti_collect.urllib.request, "urlopen", boom)
    assert iti_collect.fetch_aihot_by_query(["Anthropic"]) == []


def test_fetch_aihot_by_query_empty_entities():
    """空 entities → []."""
    assert iti_collect.fetch_aihot_by_query([]) == []
