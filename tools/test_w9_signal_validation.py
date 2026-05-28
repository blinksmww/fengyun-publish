"""
test_w9_signal_validation.py — W9 验收 harness 冒烟测试 + 反误砍守护

跑在真 parquet 上(2723 篇,aid join read_pct)。验证 harness 结构 + 核心结论:
砍掉的维度 proxy 不应有强显著正相关(否则 = 误砍了真信号)。
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

import w9_signal_validation as w9v  # noqa: E402


def test_harness_runs_and_structure():
    rep = w9v.run()
    assert rep["n_heldout"] == 50
    assert rep["n_train"] + rep["n_heldout"] == rep["n_total"]
    assert rep["n_total"] > 2000, "应跑在真 parquet(2723)上"
    assert len(rep["dims"]) >= 6
    for label, d in rep["dims"].items():
        if "error" in d:
            continue
        for k in ("overall_rho", "heldout_rho", "action", "per_account", "fold_rho_mean"):
            assert k in d, f"{label} 缺字段 {k}"
    assert "cut_dim_strong_signal_flags" in rep


def test_cut_dims_have_no_strong_signal():
    """反误砍守护:被砍维度的 proxy 不应有 |ρ|≥0.15 且显著的相关(否则砍前要复核)."""
    rep = w9v.run()
    real_flags = [f for f in rep["cut_dim_strong_signal_flags"] if not f.startswith("none")]
    assert not real_flags, f"砍掉的维度 proxy 疑似有真信号,需复核: {real_flags}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
