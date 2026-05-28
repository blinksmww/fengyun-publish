"""
ship_complete_check.py — W4 Stop hook(arch-refactor-v1, 2026-05-27)

由 .claude/settings.json 的 Stop 触发(agent 结束本轮回复时)。
行为(**咨询性,不阻断**,exit 0):
  - stop_hook_active=true(已是 hook 续跑)→ exit 0 防循环
  - 找最近活跃的 output/runs/<slug>/(有 invocation 的)
  - 若已有 render.invocation.json → ship 完整,exit 0
  - 若 6 件 pre-publish 齐全但缺 render → stderr WARN(准备好了没推草稿),exit 0

为何不 exit 2 阻断:Stop hook 阻断会把 session 困在续跑循环里,且「停在 cover 后」未必是错
(用户可能只想到封面)。本 hook 是 invocation log 的完整性消费者 + 异常可见性,
真正的硬阻断在 gate.py(PreToolUse 拦推草稿)。invariant #4:它真读真校验 invocation log。

CLI 直跑:`python tools/ship_complete_check.py [--slug X]`。
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
import invocation_log as ilog  # noqa: E402

PRE_PUBLISH = ["iti", "writer", "verify", "critic_b_huashu", "critic_c_content_judge", "cover"]


def _read_stop_payload() -> dict | None:
    try:
        if sys.stdin.isatty():
            return None
        raw = sys.stdin.read()
        if not raw.strip():
            return None
        return json.loads(raw)
    except (ValueError, OSError):
        return None


def _most_recent_run() -> Path | None:
    if not ilog.RUNS_ROOT.exists():
        return None
    cand = [
        d for d in ilog.RUNS_ROOT.iterdir()
        if d.is_dir() and any(d.glob("*.invocation.json"))
    ]
    if not cand:
        return None
    return max(cand, key=lambda d: d.stat().st_mtime)


def check_run(slug: str) -> tuple[bool, str]:
    """返回 (complete, message)。complete=有 render 或无活跃 run。"""
    loaded = ilog.load_run(slug)
    if not loaded:
        return True, f"run '{slug}' 无 invocation(无活跃 ship)"
    if "render" in loaded:
        return True, f"run '{slug}' 已 render — ship 完整"
    have = [s for s in PRE_PUBLISH if s in loaded]
    if len(have) == len(PRE_PUBLISH):
        return False, (
            f"run '{slug}':6 件 pre-publish 齐全但缺 render.invocation.json — "
            f"ship 似乎没推到草稿箱(post_fengyun_publish 未跑?)"
        )
    return True, f"run '{slug}':pre-publish 进行中({len(have)}/6),非完整 ship 时点,不告警"


def main() -> int:
    ap = argparse.ArgumentParser(description="W4 Stop hook:ship 完整性咨询检查")
    ap.add_argument("--slug", default=None, help="直接检查某 slug(CLI 调试)")
    args, _ = ap.parse_known_args()

    if args.slug:
        complete, msg = check_run(args.slug)
        if not complete:
            print(f"⚠️ ship_complete_check: {msg}", file=sys.stderr)
        else:
            print(f"✅ ship_complete_check: {msg}")
        return 0  # 咨询性

    payload = _read_stop_payload()
    if payload and payload.get("stop_hook_active"):
        return 0  # 防 Stop hook 续跑循环

    run = _most_recent_run()
    if run is None:
        return 0
    complete, msg = check_run(run.name)
    if not complete:
        print(f"⚠️ ship_complete_check: {msg}", file=sys.stderr)
    return 0  # 始终放行(咨询性,硬阻断在 gate.py)


if __name__ == "__main__":
    sys.exit(main())
