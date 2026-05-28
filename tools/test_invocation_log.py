"""
test_invocation_log.py — W4 test-first（先写,此刻 invocation_log.py 还没有 → red）

覆盖:schema 合法 / sha256 确定性 / write→load round-trip / 校验缺字段 / 校验坏 hash /
      校验坏 stage / is_fresh 时效 / load_run 聚合 / hash_matches 匹配最终稿。
所有写操作走 runs_root=tmp_path,不污染真 output/runs/。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from invocation_log import (
    SCHEMA_PATH,
    load_schema,
    sha256_text,
    hash_file,
    validate_invocation,
    write_invocation,
    load_invocation,
    load_run,
    is_fresh,
    hash_matches,
)


def _good(**over) -> dict:
    base = {
        "stage": "writer",
        "skill_name": "fengyun-writer",
        "started_at": "2026-05-27T10:00:00+00:00",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "version": "v1",
        "round": 1,
        "input_hash": "sha256:" + "a" * 64,
        "output_files": ["output/drafts/x-v0.md"],
        "result": "written",
        "summary": "test",
    }
    base.update(over)
    return base


def test_schema_file_valid_json():
    assert SCHEMA_PATH.exists()
    s = load_schema()
    assert isinstance(s, dict)
    assert "required" in s and "stage" in s["required"]
    assert "input_hash" in s["required"]


def test_sha256_text_deterministic():
    a = sha256_text("hello 风云")
    b = sha256_text("hello 风云")
    assert a == b
    assert a.startswith("sha256:")
    assert len(a) == len("sha256:") + 64


def test_validate_good():
    ok, errs = validate_invocation(_good())
    assert ok, errs
    assert errs == []


def test_validate_missing_key():
    obj = _good()
    del obj["input_hash"]
    ok, errs = validate_invocation(obj)
    assert not ok
    assert any("input_hash" in e for e in errs)


def test_validate_bad_input_hash():
    ok, errs = validate_invocation(_good(input_hash="not-a-hash"))
    assert not ok
    assert any("input_hash" in e for e in errs)


def test_validate_bad_stage():
    ok, errs = validate_invocation(_good(stage="bogus_stage"))
    assert not ok
    assert any("stage" in e for e in errs)


def test_write_and_load_roundtrip(tmp_path):
    p = write_invocation(
        slug="test-w4",
        stage="writer",
        skill_name="fengyun-writer",
        version="v1",
        round=1,
        input_hash="sha256:" + "b" * 64,
        output_files=["output/drafts/test-w4-v0.md"],
        result="written",
        summary="round-trip",
        runs_root=tmp_path,
    )
    assert p.exists()
    assert p.name == "writer.invocation.json"
    obj = load_invocation("test-w4", "writer", runs_root=tmp_path)
    assert obj is not None
    ok, errs = validate_invocation(obj)
    assert ok, errs
    assert obj["stage"] == "writer"
    assert obj["result"] == "written"


def test_load_invocation_missing_returns_none(tmp_path):
    assert load_invocation("nope", "writer", runs_root=tmp_path) is None


def test_load_run_aggregates(tmp_path):
    write_invocation(slug="r", stage="iti", skill_name="fengyun-iti", version="v1",
                     round=1, input_hash="sha256:" + "c" * 64, output_files=[],
                     result="collected", summary="", runs_root=tmp_path)
    write_invocation(slug="r", stage="cover", skill_name="fengyun-cover", version="v1",
                     round=1, input_hash="sha256:" + "d" * 64, output_files=[],
                     result="covered", summary="", runs_root=tmp_path)
    run = load_run("r", runs_root=tmp_path)
    assert set(run.keys()) == {"iti", "cover"}
    assert run["iti"]["result"] == "collected"


def test_is_fresh():
    # 窗口 2h(W10 教训:慢流程 >1h 时早期 stage 的 invocation 不应被误判过期 → gate 卡死)
    fresh_now = _good(finished_at=datetime.now(timezone.utc).isoformat())
    fresh_90min = _good(finished_at=(datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat())
    stale_3h = _good(finished_at=(datetime.now(timezone.utc) - timedelta(hours=3)).isoformat())
    assert is_fresh(fresh_now) is True
    assert is_fresh(fresh_90min) is True    # 90min < 2h → 仍新鲜(旧 1h 窗口会误判过期)
    assert is_fresh(stale_3h) is False      # 3h > 2h → 过期
    # 显式窗口参数仍可覆盖默认(回归保护)
    assert is_fresh(fresh_90min, max_age=3600) is False  # 传 1h 窗口则 90min 算过期


def test_hash_matches(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text("风云的最终稿 v3", encoding="utf-8")
    obj = _good(input_hash=hash_file(draft))
    assert hash_matches(obj, draft) is True
    draft.write_text("被偷偷改过的内容", encoding="utf-8")
    assert hash_matches(obj, draft) is False
