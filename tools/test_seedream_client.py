"""
test_seedream_client.py — W7 seedream_client 薄客户端 test-first 单测

不真发网络(全 mock _call_seedream_once / urlopen)、不依赖真实
assets/placeholder-sketch.png(用 tmp_path 造 + monkeypatch PLACEHOLDER_SRC)、
跨平台(pathlib + tmp_path)。

覆盖(对齐 wave_07_cover_redesign.md §B.4):
  1. extract_title_subtitle 截断(>14→13+…,>22→20+…)+ 正常不截断 + H1 fallback
  2. placeholder fallback:ARK 单次调用全部抛异常 → out_path 落 placeholder
     + size ≥ 5KB + placeholder_used=True
  3. retry 指数退避序列:mock 失败,patch time.sleep 记录 → 断言 [1,2,4]
  4. prompt 透传:捕获传给 ARK 的 payload → 断言 payload["prompt"] == 原始 prompt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

import seedream_client  # noqa: E402
from seedream_client import (  # noqa: E402
    extract_title_subtitle,
    generate_cover,
    BACKOFF_SECONDS,
)

# gate.py 的物理下限阈值(Round 25 Newton 补丁);独立写死避免引 gate 依赖。
IMAGE_MIN_SIZE_BYTES = 5 * 1024


# ============================================================
# helpers
# ============================================================

def _make_draft(tmp_path: Path, fm: str, body: str = "# H1 标题\n\n正文\n") -> Path:
    draft = tmp_path / "draft.md"
    if fm is None:
        draft.write_text(body, encoding="utf-8")
    else:
        draft.write_text(f"---\n{fm}\n---\n\n{body}", encoding="utf-8")
    return draft


def _make_fake_placeholder(tmp_path: Path, size: int = 6 * 1024) -> Path:
    """造一个 ≥ 5KB 的假 placeholder 源(不依赖真实 asset)。"""
    src = tmp_path / "fake-placeholder.png"
    src.write_bytes(b"\x89PNG\r\n" + b"X" * size)  # > 5KB
    return src


# ============================================================
# 1. extract_title_subtitle 截断
# ============================================================

def test_extract_title_subtitle_truncation(tmp_path):
    """>14 字标题 → 13+「…」;>22 字副标 → 20+「…」;正常不截断;H1 fallback。"""
    # 长标题(20 字)+ 长 digest(30 字)→ 双截断
    long_title = "零一二三四五六七八九十甲乙丙丁戊己庚辛"  # 20 字
    long_digest = "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥一二三四五六七八九"  # 30 字
    draft = _make_draft(tmp_path, f"title: {long_title}\ndigest: {long_digest}")
    title, subtitle = extract_title_subtitle(draft)
    assert len(title) == 14, f"截断后应 13 字 + 省略号 = 14,实际 {len(title)}: {title!r}"
    assert title == long_title[:13] + "…"
    assert len(subtitle) == 21, f"截断后应 20 字 + 省略号 = 21,实际 {len(subtitle)}: {subtitle!r}"
    assert subtitle == long_digest[:20] + "…"

    # 正常长度(≤14 / ≤22)→ 不截断
    draft2 = _make_draft(tmp_path, "title: 短标题\ndigest: 一句话副标")
    t2, s2 = extract_title_subtitle(draft2)
    assert t2 == "短标题"
    assert s2 == "一句话副标"
    assert "…" not in t2 and "…" not in s2

    # 边界:正好 14 字标题不截断,15 字才截断
    title14 = "零一二三四五六七八九十甲乙丙"  # 14 字
    draft3 = _make_draft(tmp_path, f"title: {title14}")
    t3, _ = extract_title_subtitle(draft3)
    assert t3 == title14, "正好 14 字不应截断"

    # H1 fallback:无 frontmatter title → 取第一个 H1
    draft4 = _make_draft(tmp_path, "author: 研究Agent的云", body="# 从 H1 抽的标题\n\n正文\n")
    t4, _ = extract_title_subtitle(draft4)
    assert t4 == "从 H1 抽的标题", f"无 frontmatter title 应 fallback H1,实际 {t4!r}"

    # 完全无 frontmatter,直接 H1
    draft5 = _make_draft(tmp_path, None, body="# 纯正文标题\n\n内容\n")
    t5, _ = extract_title_subtitle(draft5)
    assert t5 == "纯正文标题"


# ============================================================
# 2. placeholder fallback
# ============================================================

def test_placeholder_fallback(tmp_path, monkeypatch):
    """mock ARK 单次调用全部抛异常 → out_path 落 placeholder + size ≥ 5KB
    + placeholder_used=True。用 tmp 造 placeholder 源(不依赖真实 asset)。"""
    fake_src = _make_fake_placeholder(tmp_path, size=6 * 1024)
    monkeypatch.setattr(seedream_client, "PLACEHOLDER_SRC", fake_src)
    monkeypatch.setattr(seedream_client.time, "sleep", lambda *_a, **_k: None)  # 不真等
    # 单次调用全抛异常
    monkeypatch.setattr(
        seedream_client, "_call_seedream_once",
        mock.Mock(side_effect=RuntimeError("ARK boom")),
    )

    out_path = tmp_path / "out" / "cover.png"
    result = generate_cover("任意 prompt", "16:9", out_path, max_retries=3)

    assert result["ok"] is True, f"placeholder 落盘成功应 ok=True,实际 {result}"
    assert result["placeholder_used"] is True
    assert result["path"] == str(out_path)
    assert out_path.exists(), "out_path 应落 placeholder"
    assert out_path.stat().st_size >= IMAGE_MIN_SIZE_BYTES, \
        f"placeholder size {out_path.stat().st_size} < 5KB"
    # 全失败但走了 fallback,last_error 仍保留(audit trail)
    assert result["last_error"] == "ARK boom"
    # 尝试了 max_retries + 1 次
    assert len(result["attempts"]) == 4
    assert all(a["ok"] is False for a in result["attempts"])


def test_placeholder_source_missing_no_crash(tmp_path, monkeypatch):
    """placeholder 源也不存在 → ok=False + placeholder_used=False,不 crash。"""
    missing_src = tmp_path / "does-not-exist.png"
    monkeypatch.setattr(seedream_client, "PLACEHOLDER_SRC", missing_src)
    monkeypatch.setattr(seedream_client.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(
        seedream_client, "_call_seedream_once",
        mock.Mock(side_effect=RuntimeError("ARK boom")),
    )

    out_path = tmp_path / "out" / "cover.png"
    result = generate_cover("p", "16:9", out_path, max_retries=2)
    assert result["ok"] is False
    assert result["placeholder_used"] is False
    assert result["path"] is None
    assert not out_path.exists()


# ============================================================
# 3. retry 指数退避序列
# ============================================================

def test_retry_exponential_backoff(tmp_path, monkeypatch):
    """全失败:patch time.sleep 记录调用参数 → 断言 sleep 序列是 [1,2,4]。"""
    # placeholder 源造一个(避免 fallback 噪音),但本测点关注 sleep 序列
    fake_src = _make_fake_placeholder(tmp_path)
    monkeypatch.setattr(seedream_client, "PLACEHOLDER_SRC", fake_src)

    sleep_calls = []
    monkeypatch.setattr(seedream_client.time, "sleep",
                        lambda s: sleep_calls.append(s))
    monkeypatch.setattr(
        seedream_client, "_call_seedream_once",
        mock.Mock(side_effect=RuntimeError("fail")),
    )

    out_path = tmp_path / "cover.png"
    generate_cover("p", "16:9", out_path, max_retries=3)

    # max_retries=3 → 4 次尝试,前 3 次失败后各 sleep 一次 → [1,2,4]
    assert sleep_calls == [1, 2, 4], f"sleep 序列应 [1,2,4],实际 {sleep_calls}"
    assert sleep_calls == BACKOFF_SECONDS

    # 前缀验证:max_retries=2 → 3 次尝试,sleep [1,2]
    sleep_calls.clear()
    generate_cover("p", "16:9", out_path, max_retries=2)
    assert sleep_calls == [1, 2], f"max_retries=2 sleep 应 [1,2],实际 {sleep_calls}"


def test_retry_succeeds_after_failures_changes_seed(tmp_path, monkeypatch):
    """前 2 次失败、第 3 次成功 → ok 且每次失败换了随机 seed。"""
    monkeypatch.setattr(seedream_client.time, "sleep", lambda *_a, **_k: None)
    seen_seeds = []

    def fake_call(prompt, out_path, seed=None):
        seen_seeds.append(seed)
        if len(seen_seeds) < 3:
            raise RuntimeError("transient")
        Path(out_path).write_bytes(b"img")
        return {"seed": 777, "elapsed": 0.1, "url": "http://x"}

    monkeypatch.setattr(seedream_client, "_call_seedream_once", fake_call)

    out_path = tmp_path / "cover.png"
    result = generate_cover("p", "16:9", out_path, seed=42, max_retries=3)
    assert result["ok"] is True
    assert result["placeholder_used"] is False
    assert result["seed"] == 777
    # 首次用传入 seed=42,后续 retry 换了随机 seed(非 42)
    assert seen_seeds[0] == 42
    assert seen_seeds[1] != 42 and seen_seeds[2] != 42


# ============================================================
# 4. prompt 透传
# ============================================================

def test_prompt_passthrough(tmp_path, monkeypatch):
    """捕获传给 ARK 的 payload → payload["prompt"] == 原始 prompt(无模板 replace)。
    深入到 urlopen 层验证真正进 HTTP body 的 prompt 字段。"""
    raw_prompt = "横幅 16:9,手绘 sketchnote 封面,暖米 #F8F0E0 底,陶土橙 #D97757,标题「测试」"

    # 给 _call_seedream_once 注入 ARK_KEY + 假 urlopen / urlretrieve,捕获 payload
    monkeypatch.setattr(seedream_client, "ARK_KEY", "test-key")

    captured = {}

    class _FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(
                {"data": [{"url": "http://example/img.png", "seed": 123}]}
            ).encode("utf-8")

    def fake_urlopen(req, context=None, timeout=None):
        # req.data 是 json.dumps(payload).encode()
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        return _FakeResp()

    def fake_urlretrieve(url, filename):
        Path(filename).write_bytes(b"img-bytes")

    monkeypatch.setattr(seedream_client.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(seedream_client.urllib.request, "urlretrieve", fake_urlretrieve)
    monkeypatch.setattr(seedream_client.time, "sleep", lambda *_a, **_k: None)

    out_path = tmp_path / "cover.png"
    result = generate_cover(raw_prompt, "16:9", out_path, seed=99, max_retries=0)

    assert result["ok"] is True
    assert result["placeholder_used"] is False
    # 关键断言:进 payload 的 prompt 与原始 prompt 逐字符相同(证明透传,无 .replace)
    assert captured["payload"]["prompt"] == raw_prompt
    # 其余 payload 形状忠实迁移
    assert captured["payload"]["size"] == "2K"
    assert captured["payload"]["watermark"] is False
    assert captured["payload"]["response_format"] == "url"
    assert captured["payload"]["model"] == seedream_client.MODEL
    assert captured["payload"]["seed"] == 99


def test_sidecar_written_only_when_anchor_nonempty(tmp_path, monkeypatch):
    """成功 + style_anchor 非空 → 写 <out>.style_anchor.txt(内容=入参,无签名);
    style_anchor=None → 不写。"""
    monkeypatch.setattr(seedream_client.time, "sleep", lambda *_a, **_k: None)

    def fake_call(prompt, out_path, seed=None):
        Path(out_path).write_bytes(b"img")
        return {"seed": 1, "elapsed": 0.1, "url": "http://x"}

    monkeypatch.setattr(seedream_client, "_call_seedream_once", fake_call)

    # 有 anchor → 写 sidecar,内容就是入参(无 cloud signature 硬编)
    anchor = "warm sketchnote hand-drawn, cream #F8F0E0, terracotta #D97757 accent"
    out1 = tmp_path / "a.png"
    generate_cover("p", "16:9", out1, style_anchor=anchor, max_retries=0)
    sidecar1 = out1.with_suffix(".style_anchor.txt")
    assert sidecar1.exists()
    content = sidecar1.read_text(encoding="utf-8")
    assert content == anchor
    assert "cloud signature" not in content and "云" not in content

    # 无 anchor → 不写
    out2 = tmp_path / "b.png"
    generate_cover("p", "16:9", out2, style_anchor=None, max_retries=0)
    assert not out2.with_suffix(".style_anchor.txt").exists()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
