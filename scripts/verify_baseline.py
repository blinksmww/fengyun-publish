#!/usr/bin/env python3
"""
verify_baseline.py — 新分支重构每 wave 收尾的通用验收脚本

W0 创建,后续每 wave 完工前必跑。通过才能 commit 进新分支。

当前跑 3 件事:
1. pytest 跑 tools/test_*.py 所有测试,确认现有行为不被打破
2. fengyun_lint 对 huashu corpus 抽样 5 篇,确认 lint 流程不 crash
3. invocation log schema + validator 自检(W4 扩展)

W6 完工后会扩展第 4 件:ship.py SDK 编排 smoke test。

退出码:
- 0 = 全过(可以 commit)
- 1 = 任一失败(不能 commit,先修;包含 pytest 失败 / lint 失败 / 环境异常)

(原 docstring 提及 exit 2 = 环境异常,但 main() 实现里没分流 — 已删除,
 遵守 invariant #4「0 消费者 = 0 生产」:没人区分 1 vs 2,就不假装支持)

用法:
    python scripts/verify_baseline.py

可选参数:
    --skip-pytest    跳过 pytest(开发期间快速检查 lint)
    --skip-lint      跳过 lint baseline(只想跑 pytest)
    --verbose        打印每个 lint 文件的详细输出
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"
CORPUS_HUASHU = ROOT / "corpus" / "raw" / "huashu"


# Known baseline failures(W0 接受为已知缺陷,后续 wave 一起处理)
# W2:test_round26_fixes.py 的 B 组 6 个(fix_punctuation_text/_file)已修复回归 —
#     fix_punctuation.py 补回两个函数,deselect 名单清空(见 REFACTOR_PLAN.md W0 缺陷表)。
# 当前无已知 baseline failure;后续若再出现,在此登记 nodeid 并在 REFACTOR_PLAN.md 留档。
KNOWN_FAILING_TESTS: list[str] = []


def run_pytest() -> tuple[bool, str]:
    """跑 tools/test_*.py 所有测试(跳过 KNOWN_FAILING_TESTS).

    Returns:
        (passed, summary)
    """
    if not TOOLS_DIR.exists():
        return False, f"tools/ 目录不存在: {TOOLS_DIR}"

    test_files = list(TOOLS_DIR.glob("test_*.py"))
    if not test_files:
        return False, f"tools/test_*.py 一个文件都没有"

    cmd = ["python", "-m", "pytest", str(TOOLS_DIR), "-q", "--tb=line"]
    # 加 --deselect 跳过 known failure
    for known in KNOWN_FAILING_TESTS:
        cmd.extend(["--deselect", known])
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            encoding="utf-8", errors="replace", cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        return False, "pytest 超时 (>300s)"
    except FileNotFoundError:
        return False, "pytest 没装,跑 pip install pytest"

    if result.returncode != 0:
        tail = result.stdout[-800:] + result.stderr[-400:]
        return False, f"pytest 失败:\n{tail}"

    # 提取「N passed」摘要
    last_line = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    known_count = len(KNOWN_FAILING_TESTS)
    suffix = (
        f" (跳过 {known_count} 个 known baseline failure — 见 REFACTOR_PLAN.md)"
        if known_count else ""
    )
    return True, f"pytest PASS / {len(test_files)} test files / {last_line}{suffix}"


def run_lint_baseline(verbose: bool = False) -> tuple[bool, str]:
    """对 huashu corpus 抽 5 篇跑 fengyun_lint,确认不 crash.

    Returns:
        (passed, summary)
    """
    if not CORPUS_HUASHU.exists():
        return False, f"huashu corpus 不存在: {CORPUS_HUASHU}"

    md_files = list(CORPUS_HUASHU.glob("*.md"))
    if len(md_files) < 5:
        return False, f"huashu corpus 不足 5 篇 (只有 {len(md_files)})"

    random.seed(42)  # 固定 seed,可复现
    sampled = random.sample(md_files, 5)

    lint_script = TOOLS_DIR / "fengyun_lint.py"
    if not lint_script.exists():
        return False, f"fengyun_lint.py 不存在"

    crashes = []
    for md in sampled:
        cmd = ["python", str(lint_script), str(md)]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                encoding="utf-8", errors="replace", cwd=str(ROOT),
            )
            if verbose:
                print(f"  [{md.name[:40]}] exit={result.returncode}")
            # fengyun_lint 可能 exit 0 / 1 / 2 都正常(violations 数量不同)
            # 只 fail 在 crash(exit code > 100 或 stderr 有 Traceback)
            if "Traceback" in result.stderr:
                crashes.append(f"{md.name}: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            crashes.append(f"{md.name}: TIMEOUT")
        except Exception as e:
            crashes.append(f"{md.name}: {type(e).__name__}: {e}")

    if crashes:
        return False, f"lint baseline 失败:\n" + "\n".join(crashes)

    return True, f"lint baseline PASS / 5 篇 huashu corpus 全部无 crash"


def run_invocation_schema_check() -> tuple[bool, str]:
    """W4:invocation log schema + validator 自检.

    schema 合法 + 好样本通过 + 坏样本(缺 input_hash)被拦 → 证明消费链健康.
    """
    import json
    schema_path = ROOT / "assets" / "run_log.schema.json"
    if not schema_path.exists():
        return False, f"run_log.schema.json 不存在: {schema_path}"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return False, f"run_log.schema.json 非法 JSON: {e}"
    if "stage" not in schema.get("required", []):
        return False, "run_log.schema.json 缺 required/stage"

    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    try:
        import invocation_log as ilog
    except Exception as e:  # noqa: BLE001
        return False, f"invocation_log 导入失败: {e}"

    good = {
        "stage": "writer", "skill_name": "fengyun-writer",
        "started_at": "2026-05-27T10:00:00+00:00",
        "finished_at": "2026-05-27T10:05:00+00:00",
        "version": "v1", "round": 1,
        "input_hash": "sha256:" + "a" * 64,
        "output_files": [], "result": "written", "summary": "self-check",
    }
    ok, errs = ilog.validate_invocation(good)
    if not ok:
        return False, f"好样本被误判非法: {errs}"
    bad = dict(good)
    del bad["input_hash"]
    ok2, _ = ilog.validate_invocation(bad)
    if ok2:
        return False, "坏样本(缺 input_hash)未被拦 — validator 失效"

    return True, "invocation log schema + validator 自检 PASS(好样本过 / 坏样本拦)"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--skip-pytest", action="store_true", help="跳过 pytest")
    ap.add_argument("--skip-lint", action="store_true", help="跳过 lint baseline")
    ap.add_argument("--skip-invocation", action="store_true", help="跳过 invocation schema 自检")
    ap.add_argument("--verbose", action="store_true", help="详细输出")
    args = ap.parse_args()

    print("=" * 60)
    print("verify_baseline.py — 新分支重构验收脚本")
    print(f"  ROOT: {ROOT}")
    print("=" * 60)

    all_pass = True

    # Check 1: pytest
    if not args.skip_pytest:
        print("\n[1/3] pytest tools/test_*.py ...")
        ok, msg = run_pytest()
        print(f"  → {msg}")
        if not ok:
            all_pass = False
    else:
        print("\n[1/3] pytest SKIPPED")

    # Check 2: lint baseline
    if not args.skip_lint:
        print("\n[2/3] lint baseline (5 篇 huashu corpus) ...")
        ok, msg = run_lint_baseline(verbose=args.verbose)
        print(f"  → {msg}")
        if not ok:
            all_pass = False
    else:
        print("\n[2/3] lint baseline SKIPPED")

    # Check 3: invocation log schema 自检(W4)
    if not args.skip_invocation:
        print("\n[3/3] invocation log schema + validator 自检 ...")
        ok, msg = run_invocation_schema_check()
        print(f"  → {msg}")
        if not ok:
            all_pass = False
    else:
        print("\n[3/3] invocation schema SKIPPED")

    print("\n" + "=" * 60)
    if all_pass:
        print("[PASS] ALL CHECKS PASSED — 可以 commit 进新分支")
        print("=" * 60)
        return 0
    else:
        print("[FAIL] FAILED — 修完再跑 verify_baseline.py")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
