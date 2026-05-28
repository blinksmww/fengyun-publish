"""
validate_run_log.py — W4 PostToolUse hook(arch-refactor-v1, 2026-05-27)

由 .claude/settings.json 的 PostToolUse(Write|Edit|MultiEdit)触发。
行为:
  - 解析 hook stdin payload,取被写文件路径
  - 若不是 *.invocation.json → exit 0 放行(只管 invocation log)
  - 是 invocation.json → 按 run_log.schema.json 校验
      合法 → exit 0
      非法 JSON / schema 不过 → exit 2 + stderr(把错误回给 Claude)

invariant #4:这是 invocation log 的真消费者之一(写出脏 invocation 立即拦)。
也支持 CLI 直跑:`python tools/validate_run_log.py <path>`。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
import invocation_log as ilog  # noqa: E402


def _extract_written_path() -> str | None:
    """从 PostToolUse hook stdin payload 取被写文件路径。"""
    try:
        if sys.stdin.isatty():
            return None
        raw = sys.stdin.read()
        if not raw.strip():
            return None
        payload = json.loads(raw)
    except (ValueError, OSError):
        return None
    ti = payload.get("tool_input", {}) or {}
    return ti.get("file_path") or ti.get("path") or payload.get("file_path")


def main() -> int:
    # CLI 直跑优先
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        fp = sys.argv[1]
    else:
        fp = _extract_written_path()

    if not fp or not str(fp).endswith(".invocation.json"):
        return 0  # 非 invocation log → 放行

    p = Path(fp)
    if not p.exists():
        return 0  # 文件还没落地(被删/移)→ 不误伤

    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:
        print(f"❌ invocation log 非法 JSON:{p}:{e}", file=sys.stderr)
        return 2

    ok, errs = ilog.validate_invocation(obj)
    if ok:
        return 0

    print(f"❌ invocation log schema 不合法:{p}", file=sys.stderr)
    print("   依据:assets/run_log.schema.json", file=sys.stderr)
    for e in errs:
        print(f"   - {e}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
