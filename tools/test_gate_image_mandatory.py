"""Round 25 文内图强制必选 — gate.py + illustrate_decider.py 验收测试

SPEC: docs/SPEC_ROUND25_IMAGE_MANDATORY.md
W4(2026-05-27): gate 的 pass_flag/防伪检查迁到 invocation log。本测试:
  - frontmatter 精简为 metadata + 物理产物指针(image_paths/cover_path/image_at_h2_indices)
  - 每个 gate 测试先造 6 个合法 invocation(_setup_valid_invocations),
    使「唯一的 block 原因」就是被测的那个 image 问题。
覆盖:
  1. image_paths 缺失 / 空 list → gate BLOCK
  2. image_paths 文件不存在 → gate BLOCK
  3. image_paths 文件 size < 5 KB → gate BLOCK(Newton 补丁)
  4. image_paths 含 placeholder(≥ 5 KB)→ gate PASS
  5. image_generation_degraded=true → gate BLOCK(Round 25 废弃)
  6. illustrate_decider should_illustrate=false → placeholder fallback(不返回 [])
  7. illustrate_decider count=0 → placeholder fallback
"""
from __future__ import annotations
import sys
import shutil
import tempfile
from pathlib import Path

import pytest

# 让 test 在 tools/ 目录跑也能 import
sys.path.insert(0, str(Path(__file__).parent))

from gate import check_draft, IMAGE_MIN_SIZE_BYTES
from invocation_log import write_invocation, hash_file, run_dir
from illustrate_decider import (
    generate_from_decision,
    _copy_placeholder_to_output,
    PLACEHOLDER_SRC,
    OUT_DIR,
)

TEST_SLUG = "round25-test"


# ============================================================
# fixtures
# ============================================================

def _make_draft(tmpdir: Path, fm_extras: dict) -> Path:
    """生成一个最小 draft(W4 精简 frontmatter:metadata + 物理产物指针),merge fm_extras。"""
    base = {
        "title": "Round 25 测试",
        "digest": "Round 25 测试摘要",
        "author": "研究Agent的云",
        "slug": TEST_SLUG,
        "date": "2026-05-25",
        "north_star": "测试文内图强制必选",
        # 物理产物指针(W4 spec §1.1 留 frontmatter)
        "cover_path": "assets/placeholder-sketch.png",  # 复用 placeholder 当 cover(测试用)
        "image_at_h2_indices": "[1]",
    }
    base.update({k: v for k, v in fm_extras.items() if v is not None})

    fm_lines = []
    for k, v in base.items():
        if k in fm_extras and fm_extras[k] is None:
            continue  # None = 强制不写这个字段
        if isinstance(v, list):
            fm_lines.append(f"{k}: " + str(v).replace("'", '"'))
        else:
            fm_lines.append(f"{k}: {v}")

    fm_text = "\n".join(fm_lines)
    draft = tmpdir / "round25-test-v0.md"
    draft.write_text(
        f"---\n{fm_text}\n---\n\n# 测试正文\n\n这是一篇测试文章。\n",
        encoding="utf-8",
    )
    return draft


def _setup_valid_invocations(draft: Path, slug: str = TEST_SLUG) -> None:
    """W4:为 slug 造 6 个合法 + 新鲜的 pre-publish invocation。
    FINAL_DRAFT_STAGES(verify/critic_b/critic_c/cover)用当前 draft 的真实 hash;
    iti/writer 用占位 hash(它们 input 是 research/前一版,gate 不强制匹配最终稿)。
    verify result=ship(过 SHIP_DECISIONS)。"""
    draft_hash = hash_file(draft)
    other_hash = "sha256:" + "0" * 64
    specs = [
        ("iti", "fengyun-iti", other_hash, "collected"),
        ("writer", "fengyun-writer", other_hash, "written"),
        ("verify", "orchestrator", draft_hash, "ship"),
        ("critic_b_huashu", "huashu-perspective", draft_hash, "ship"),
        ("critic_c_content_judge", "content-judge", draft_hash, "sign"),
        ("cover", "fengyun-cover", draft_hash, "covered"),
    ]
    for stage, skill, ih, result in specs:
        write_invocation(slug=slug, stage=stage, skill_name=skill, version="v1",
                         round=1, input_hash=ih, output_files=[], result=result,
                         summary="test")


def _cleanup_run(slug: str = TEST_SLUG) -> None:
    shutil.rmtree(run_dir(slug), ignore_errors=True)


# ============================================================
# gate.py tests(image 物理检查 — 在 invocation 全合法前提下)
# ============================================================

def test_image_paths_missing_blocks():
    """Bug case: image_paths 字段完全缺失 → gate BLOCK"""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        draft = _make_draft(tmpdir, {})  # 不提供 image_paths
        _setup_valid_invocations(draft)
        try:
            passed, missing = check_draft(draft)
            assert not passed, f"image_paths 缺失应被 BLOCK,实际 PASS。missing={missing}"
            assert any("image_paths" in m and "缺失或空" in m for m in missing), \
                f"missing 列表应含 image_paths 缺失提示。实际:{missing}"
        finally:
            _cleanup_run()


def test_image_paths_empty_blocks():
    """Bug case: image_paths=[] 空 list → gate BLOCK"""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        draft = _make_draft(tmpdir, {"image_paths": "[]"})
        _setup_valid_invocations(draft)
        try:
            passed, missing = check_draft(draft)
            assert not passed, "image_paths=[] 应被 BLOCK,实际 PASS"
            assert any("image_paths" in m and ("缺失或空" in m or "空" in m) for m in missing)
        finally:
            _cleanup_run()


def test_image_paths_nonexistent_file_blocks():
    """image_paths 指向不存在文件 → gate BLOCK"""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        draft = _make_draft(tmpdir, {
            "image_paths": '["output/images/nonexistent-fake.png"]'
        })
        _setup_valid_invocations(draft)
        try:
            passed, missing = check_draft(draft)
            assert not passed
            assert any("不存在" in m for m in missing)
        finally:
            _cleanup_run()


def test_image_paths_tiny_file_blocks():
    """image_paths 文件 size < 5 KB → gate BLOCK(Newton 补丁)"""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        tiny = tmpdir / "tiny.png"
        tiny.write_bytes(b"X" * 1024)  # 1 KB
        draft = _make_draft(tmpdir, {"image_paths": f'["{tiny.as_posix()}"]'})
        _setup_valid_invocations(draft)
        try:
            passed, missing = check_draft(draft)
            assert not passed, "size < 5KB 应被 BLOCK,实际 PASS"
            assert any("size" in m and "下限" in m for m in missing)
        finally:
            _cleanup_run()


def test_placeholder_passes_gate():
    """image_paths 含 placeholder(≥ 5 KB)+ invocation 全合法 → gate PASS"""
    assert PLACEHOLDER_SRC.exists(), \
        f"placeholder 不存在: {PLACEHOLDER_SRC}(跑 assets/generate_placeholder.py)"
    size = PLACEHOLDER_SRC.stat().st_size
    assert size >= IMAGE_MIN_SIZE_BYTES, \
        f"placeholder size {size} < {IMAGE_MIN_SIZE_BYTES} 阈值"

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        draft = _make_draft(tmpdir, {
            "image_paths": f'["{PLACEHOLDER_SRC.as_posix()}"]'
        })
        _setup_valid_invocations(draft)
        try:
            passed, missing = check_draft(draft)
            assert passed, f"placeholder 路径 + 合法 invocation 应 PASS,实际被 BLOCK。missing={missing}"
        finally:
            _cleanup_run()


def test_image_generation_degraded_true_blocks():
    """Round 25:image_generation_degraded=true 路径已废 → gate BLOCK"""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        draft = _make_draft(tmpdir, {
            "image_paths": f'["{PLACEHOLDER_SRC.as_posix()}"]',
            "image_generation_degraded": "true",
        })
        _setup_valid_invocations(draft)
        try:
            passed, missing = check_draft(draft)
            assert not passed, "image_generation_degraded=true 应被 BLOCK"
            assert any("degraded" in m.lower() and "废弃" in m for m in missing)
        finally:
            _cleanup_run()


# ============================================================
# illustrate_decider.py tests(不经 check_draft,W4 不受影响)
# ============================================================

def test_should_illustrate_false_fallback_to_placeholder(tmp_path):
    """skill 返回 should_illustrate=false → 强制 placeholder fallback,不返回 []
    Bug B3 修复后:placeholder 路径必须写 image_at_h2_indices,gate 才不拦。"""
    decision = {
        "should_illustrate": False,
        "count": 0,
        "prompts": [],
        "positions": [],
    }
    image_paths = generate_from_decision(decision, OUT_DIR, slug="r25-test-false")
    assert len(image_paths) >= 1, "should_illustrate=false 不应返回空,应 fallback placeholder"
    assert all(p.exists() for p in image_paths)
    assert decision.get("fallback_reason"), "fallback_reason 字段必须写入(audit trail)"
    assert decision.get("image_at_h2_indices") is not None, \
        "Bug B3:placeholder fallback 必须写 image_at_h2_indices,否则 gate.py 拦截"
    for p in image_paths:
        if p.parent == OUT_DIR and "placeholder" in p.name:
            p.unlink(missing_ok=True)


def test_prompts_empty_fallback_to_placeholder(tmp_path):
    """skill 返回 prompts=[] (count=0) → 强制 placeholder fallback"""
    decision = {
        "should_illustrate": True,
        "count": 3,
        "prompts": [],
        "positions": [],
    }
    image_paths = generate_from_decision(decision, OUT_DIR, slug="r25-test-empty-prompts")
    assert len(image_paths) >= 1
    assert decision.get("fallback_reason"), "fallback_reason 必须写入"
    assert decision.get("image_at_h2_indices") is not None, "Bug B3:必须写 indices"
    for p in image_paths:
        if p.parent == OUT_DIR and "placeholder" in p.name:
            p.unlink(missing_ok=True)


def test_write_metadata_asserts_nonempty_image_paths(tmp_path):
    """Bug B2 修复:write_metadata 接收空 image_paths 立即 AssertionError"""
    from illustrate_decider import write_metadata
    draft = tmp_path / "test-draft-empty-paths.md"
    draft.write_text("---\ntitle: test\n---\n\n# body\n", encoding="utf-8")
    decision = {"should_illustrate": False}
    with pytest.raises(AssertionError, match="Round 25 invariant"):
        write_metadata(draft, decision, [])


def test_write_metadata_writes_fallback_reason(tmp_path):
    """Bug B4 修复:placeholder 触发时,fallback_reason 写入 frontmatter(audit trail)"""
    from illustrate_decider import write_metadata
    draft = tmp_path / "test-draft-audit.md"
    draft.write_text("---\ntitle: test\nslug: test\n---\n\n# body\n", encoding="utf-8")
    decision = {
        "should_illustrate": False,
        "fallback_reason": "skill_returned_false",
        "image_at_h2_indices": [0],
        "style_anchor": None,
    }
    write_metadata(draft, decision, [PLACEHOLDER_SRC])
    content = draft.read_text(encoding="utf-8")
    assert 'fallback_reason: "skill_returned_false"' in content, \
        "Bug B4:placeholder 触发时 fallback_reason 必须写入 frontmatter"
    assert "image_at_h2_indices: [0]" in content, \
        "image_at_h2_indices 应写入 frontmatter(Bug B3 闭环)"


def test_copy_placeholder_to_output_works():
    """_copy_placeholder_to_output 直调:复制 N 张 placeholder 副本"""
    slug = "r25-test-copy"
    paths = _copy_placeholder_to_output(slug, count=3)
    assert len(paths) == 3
    for p in paths:
        assert p.exists()
        assert p.stat().st_size >= IMAGE_MIN_SIZE_BYTES
        assert "placeholder" in p.name
    for p in paths:
        p.unlink(missing_ok=True)


def test_placeholder_src_exists_and_valid_size():
    """asset placeholder 文件存在 + size ≥ 5 KB(系统级 invariant)"""
    assert PLACEHOLDER_SRC.exists(), f"placeholder asset 不存在: {PLACEHOLDER_SRC}"
    size = PLACEHOLDER_SRC.stat().st_size
    assert size >= IMAGE_MIN_SIZE_BYTES, f"placeholder size {size} < {IMAGE_MIN_SIZE_BYTES}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
