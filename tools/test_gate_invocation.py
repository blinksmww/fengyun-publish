"""W4 gate ↔ invocation log 集成测试(2026-05-27, arch-refactor-v1)

验 gate.check_draft 的 invocation 消费逻辑:
  - 缺 invocation → BLOCK
  - invocation 过期(finished_at ≥ 1h)→ BLOCK
  - 最终稿 stage 的 input_hash 不匹配当前 draft → BLOCK(防拿旧版 verdict ship 新稿)
  - verify.result 不在 {ship, force_ship} → BLOCK
  - 全合法 → PASS;force_ship 也放行
"""
from __future__ import annotations
import sys
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gate import check_draft
from invocation_log import write_invocation, hash_file, run_dir

SLUG = "w4-inv-test"


def _make_draft(tmpdir: Path) -> Path:
    fm = "\n".join([
        "title: W4 测试",
        "digest: W4 invocation gate 测试",
        "author: 研究Agent的云",
        f"slug: {SLUG}",
        "date: 2026-05-27",
        "north_star: 测试 invocation gate",
        "cover_path: assets/placeholder-sketch.png",
        "image_at_h2_indices: [1]",
        'image_paths: ["assets/placeholder-sketch.png"]',
    ])
    draft = tmpdir / f"{SLUG}-v0.md"
    draft.write_text(f"---\n{fm}\n---\n\n# 正文\n\n测试。\n", encoding="utf-8")
    return draft


def _write_all(draft: Path, *, verify_result="ship", final_hash=None, finished_at=None):
    """造 6 个 invocation。final_hash 默认当前 draft hash;finished_at 默认 now。"""
    dh = final_hash if final_hash is not None else hash_file(draft)
    other = "sha256:" + "0" * 64
    specs = [
        ("iti", other, "collected"),
        ("writer", other, "written"),
        ("verify", dh, verify_result),
        ("critic_b_huashu", dh, "ship"),
        ("critic_c_content_judge", dh, "sign"),
        ("cover", dh, "covered"),
    ]
    for stage, ih, result in specs:
        kw = {}
        if finished_at is not None:
            kw["finished_at"] = finished_at
            kw["started_at"] = finished_at
        write_invocation(slug=SLUG, stage=stage, skill_name=stage, version="v1",
                         round=1, input_hash=ih, output_files=[], result=result,
                         summary="test", **kw)


def _cleanup():
    shutil.rmtree(run_dir(SLUG), ignore_errors=True)


def test_all_valid_passes():
    with tempfile.TemporaryDirectory() as tmp:
        draft = _make_draft(Path(tmp))
        _write_all(draft)
        try:
            passed, missing = check_draft(draft)
            assert passed, f"全合法应 PASS。missing={missing}"
        finally:
            _cleanup()


def test_missing_invocation_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        draft = _make_draft(Path(tmp))
        _write_all(draft)
        # 删掉 critic_b
        (run_dir(SLUG) / "critic_b_huashu.invocation.json").unlink()
        try:
            passed, missing = check_draft(draft)
            assert not passed
            assert any("缺 invocation" in m and "critic_b_huashu" in m for m in missing), missing
        finally:
            _cleanup()


def test_stale_invocation_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        draft = _make_draft(Path(tmp))
        old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        _write_all(draft, finished_at=old)
        try:
            passed, missing = check_draft(draft)
            assert not passed
            assert any("过期" in m for m in missing), missing
        finally:
            _cleanup()


def test_hash_mismatch_blocks():
    """最终稿 stage 的 input_hash 对不上当前 draft → BLOCK(防拿旧版 verdict ship 新稿)"""
    with tempfile.TemporaryDirectory() as tmp:
        draft = _make_draft(Path(tmp))
        wrong = "sha256:" + "f" * 64
        _write_all(draft, final_hash=wrong)
        try:
            passed, missing = check_draft(draft)
            assert not passed
            assert any("input_hash 不匹配" in m for m in missing), missing
        finally:
            _cleanup()


def test_verify_not_ship_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        draft = _make_draft(Path(tmp))
        _write_all(draft, verify_result="revise")
        try:
            passed, missing = check_draft(draft)
            assert not passed
            assert any("verify.invocation.json result" in m for m in missing), missing
        finally:
            _cleanup()


def test_force_ship_passes():
    """隐藏天花板 force_ship 也放行(verify.result=force_ship)"""
    with tempfile.TemporaryDirectory() as tmp:
        draft = _make_draft(Path(tmp))
        _write_all(draft, verify_result="force_ship")
        try:
            passed, missing = check_draft(draft)
            assert passed, f"force_ship 应放行。missing={missing}"
        finally:
            _cleanup()


def test_missing_slug_blocks():
    """draft 无 slug → 无法定位 invocation log → BLOCK"""
    with tempfile.TemporaryDirectory() as tmp:
        draft = Path(tmp) / "no-slug-v0.md"
        draft.write_text(
            "---\ntitle: x\ndigest: x\nauthor: y\ndate: 2026-05-27\n"
            "north_star: z\ncover_path: assets/placeholder-sketch.png\n"
            'image_at_h2_indices: [1]\nimage_paths: ["assets/placeholder-sketch.png"]\n---\n\n# x\n',
            encoding="utf-8",
        )
        passed, missing = check_draft(draft)
        assert not passed
        assert any("slug" in m for m in missing), missing


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
