"""test_flywheel_report.py — force_ship 学习回路消费者测试(arch-refactor-v1 post-W10 follow-up)。

覆盖:scan_runs 从 W4 invocation log 聚合 / aggregate 算 force_ship 率 + B 否决 + C 挂名 +
      B/C 分歧 / 空目录不除零 / render_report smoke + 高 force_ship 率提示。
所有写操作走 tmp_path,不污染真 output/runs/。
"""
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

from invocation_log import write_invocation  # noqa: E402
from flywheel_report import scan_runs, aggregate, render_report  # noqa: E402

_H = "sha256:" + "0" * 64


def _seed_run(runs_root, slug, verify_result, b_result, c_result):
    write_invocation(slug=slug, stage="verify", skill_name="orchestrator", version="v1",
                     round=1, input_hash=_H, output_files=[], result=verify_result, runs_root=runs_root)
    write_invocation(slug=slug, stage="critic_b_huashu", skill_name="huashu-perspective", version="v1",
                     round=1, input_hash=_H, output_files=[], result=b_result, runs_root=runs_root)
    write_invocation(slug=slug, stage="critic_c_content_judge", skill_name="content-judge", version="v1",
                     round=1, input_hash=_H, output_files=[], result=c_result, runs_root=runs_root)


def test_scan_and_aggregate_force_ship_rate(tmp_path):
    _seed_run(tmp_path, "run-a", "force_ship", "no-ship", "sign")
    _seed_run(tmp_path, "run-b", "ship", "ship", "sign")
    _seed_run(tmp_path, "run-c", "force_ship", "no-ship", "sign")
    records = scan_runs(tmp_path)
    assert len(records) == 3
    agg = aggregate(records)
    assert agg["n"] == 3
    assert agg["force_ship_count"] == 2
    assert abs(agg["force_ship_rate"] - 2 / 3) < 1e-9
    assert agg["b_reject_count"] == 2     # 2 个 no-ship
    assert agg["c_sign_count"] == 3       # 3 个 sign


def test_bc_disagreement(tmp_path):
    _seed_run(tmp_path, "run-x", "force_ship", "no-ship", "sign")  # B 否 / C 挂名 → 分歧
    _seed_run(tmp_path, "run-y", "ship", "ship", "sign")           # 双过 → 一致
    agg = aggregate(scan_runs(tmp_path))
    assert agg["bc_disagree_count"] == 1


def test_scan_skips_dirs_without_verify(tmp_path):
    # 只写 iti(无 verify.invocation)的目录不算一次标准 ship,应被跳过
    write_invocation(slug="staging", stage="iti", skill_name="fengyun-iti", version="v1",
                     round=1, input_hash=_H, output_files=[], result="collected", runs_root=tmp_path)
    assert scan_runs(tmp_path) == []


def test_empty_runs_root(tmp_path):
    records = scan_runs(tmp_path)
    assert records == []
    agg = aggregate(records)
    assert agg["n"] == 0
    assert agg["force_ship_rate"] == 0.0   # 不除零


def test_render_report_high_force_ship_hint(tmp_path):
    _seed_run(tmp_path, "run-a", "force_ship", "no-ship", "sign")
    _seed_run(tmp_path, "run-b", "force_ship", "no-ship", "sign")
    records = scan_runs(tmp_path)
    md = render_report(aggregate(records), records)
    assert isinstance(md, str) and "force_ship" in md
    assert "writer SOP" in md            # 高 force_ship 率给机制层提示
    assert "run-a" in md                 # force_ship 篇目列出
