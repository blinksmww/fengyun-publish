"""
invocation_log.py — W4:invocation log 生产者 + 校验器（arch-refactor-v1，2026-05-27）

物理目的(见 docs/ARCH_REFACTOR_V1_PLAN.md A3 + REFACTOR_PLAN §1.1 invariant #3/#4):
  每个 skill / subagent / orchestrator stage 跑完,写一个 <stage>.invocation.json 到
  output/runs/<slug>/。取代旧的 ~25 个 frontmatter 防伪字段(writer_pass / *_real_run /
  *_source ...)。gate.py 是消费者(检查文件存在 + schema 合法 + input_hash 匹配当前稿 +
  finished_at < 1h)。

反 fake 升级(Newton 真 invariant):旧 frontmatter pass_flag 证明不了「critic 评的是最终稿」,
  input_hash == sha256(当前 draft) 能证明「这一轨真在这一版上跑过」。

schema 单一事实源:assets/run_log.schema.json(本模块用它驱动 validate,不引第三方 jsonschema)。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
SCHEMA_PATH = ROOT / "assets" / "run_log.schema.json"
RUNS_ROOT = ROOT / "output" / "runs"
MAX_AGE_SECONDS = 7200  # invocation 时效窗口 2h(W10 教训:完整 ship 可能 >1h,1h 窗口会让早期
                        # stage(iti/writer)的 invocation 在 gate 时已过期 → 误判「必须重跑」卡死。
                        # 末轮 stage(verify/critic/cover)另有 input_hash 兜底,新鲜度是次级守卫。)

_SCHEMA_CACHE: dict | None = None


# ============================================================
# 路径 / hash
# ============================================================

def run_dir(slug: str, runs_root: Path | None = None) -> Path:
    return (runs_root or RUNS_ROOT) / slug


def _invocation_path(slug: str, stage: str, runs_root: Path | None = None) -> Path:
    return run_dir(slug, runs_root) / f"{stage}.invocation.json"


def sha256_text(text: str) -> str:
    """返回 'sha256:<64hex>'(对文本 utf-8 编码取 sha256)。"""
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{h}"


def hash_file(path: str | Path) -> str:
    """对文件文本内容取 sha256(utf-8,errors=replace 防解码炸)。"""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    return sha256_text(text)


# ============================================================
# schema 驱动校验(不依赖第三方 jsonschema)
# ============================================================

def load_schema() -> dict:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return _SCHEMA_CACHE


def validate_invocation(obj: dict) -> tuple[bool, list[str]]:
    """按 run_log.schema.json 的 required + properties(type/enum/pattern/minLength/minimum)校验。

    返回 (ok, errors)。轻量实现,只覆盖本 schema 用到的关键字。
    """
    errs: list[str] = []
    if not isinstance(obj, dict):
        return False, ["invocation 不是 object"]

    schema = load_schema()
    required = schema.get("required", [])
    props = schema.get("properties", {})

    for key in required:
        if key not in obj:
            errs.append(f"缺必填字段:{key}")

    type_map = {
        "string": str,
        "integer": int,
        "array": list,
        "object": dict,
        "number": (int, float),
        "boolean": bool,
    }

    for key, spec in props.items():
        if key not in obj:
            continue  # 缺失已在 required 报过;非 required 缺失允许
        val = obj[key]
        exp = spec.get("type")
        # bool 是 int 的子类,integer 校验要排除 bool
        if exp == "integer" and isinstance(val, bool):
            errs.append(f"字段 {key} 应为 integer,实际 bool")
            continue
        if exp and not isinstance(val, type_map[exp]):
            errs.append(f"字段 {key} 类型应为 {exp},实际 {type(val).__name__}")
            continue
        if "enum" in spec and val not in spec["enum"]:
            errs.append(f"字段 {key} 值 {val!r} 不在 enum {spec['enum']}")
        if "pattern" in spec and isinstance(val, str):
            if not re.match(spec["pattern"], val):
                errs.append(f"字段 {key} 值 {val!r} 不匹配 pattern {spec['pattern']}")
        if "minLength" in spec and isinstance(val, str):
            if len(val) < spec["minLength"]:
                errs.append(f"字段 {key} 长度 < {spec['minLength']}")
        if "minimum" in spec and isinstance(val, (int, float)) and not isinstance(val, bool):
            if val < spec["minimum"]:
                errs.append(f"字段 {key} < minimum {spec['minimum']}")
        if exp == "array" and "items" in spec and isinstance(val, list):
            item_type = type_map.get(spec["items"].get("type"))
            if item_type and any(not isinstance(x, item_type) for x in val):
                errs.append(f"字段 {key} 数组元素类型应为 {spec['items'].get('type')}")

    return (len(errs) == 0), errs


# ============================================================
# 时效 / hash 匹配(gate.py 消费时用)
# ============================================================

def _parse_iso(ts: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_fresh(obj: dict, now: datetime | None = None, max_age: int = MAX_AGE_SECONDS) -> bool:
    """finished_at 距 now 是否 < max_age 秒。"""
    dt = _parse_iso(obj.get("finished_at", ""))
    if dt is None:
        return False
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    age = (now - dt).total_seconds()
    return 0 <= age < max_age


def hash_matches(obj: dict, draft_path: str | Path) -> bool:
    """invocation 的 input_hash 是否 == 当前 draft 文件 hash(证明这一轨跑的是这一版)。"""
    p = Path(draft_path)
    if not p.exists():
        return False
    return obj.get("input_hash") == hash_file(p)


# ============================================================
# 写 / 读
# ============================================================

def write_invocation(
    slug: str,
    stage: str,
    skill_name: str,
    version: str,
    round: int,
    input_hash: str,
    output_files: list[str],
    result: str,
    summary: str = "",
    started_at: str | None = None,
    finished_at: str | None = None,
    runs_root: Path | None = None,
) -> Path:
    """写一个 <stage>.invocation.json。started/finished 默认取当前时刻。

    写前自校验,schema 不过抛 ValueError(防写出脏 invocation)。
    """
    now = datetime.now(timezone.utc).isoformat()
    obj = {
        "stage": stage,
        "skill_name": skill_name,
        "started_at": started_at or now,
        "finished_at": finished_at or now,
        "version": version,
        "round": round,
        "input_hash": input_hash,
        "output_files": list(output_files),
        "result": result,
        "summary": summary,
    }
    ok, errs = validate_invocation(obj)
    if not ok:
        raise ValueError(f"invocation 校验失败,拒绝写入:{errs}")

    path = _invocation_path(slug, stage, runs_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_invocation(slug: str, stage: str, runs_root: Path | None = None) -> dict | None:
    path = _invocation_path(slug, stage, runs_root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def load_run(slug: str, runs_root: Path | None = None) -> dict[str, dict]:
    """加载某 slug 下所有 *.invocation.json,返回 {stage: obj}。"""
    d = run_dir(slug, runs_root)
    out: dict[str, dict] = {}
    if not d.exists():
        return out
    for f in d.glob("*.invocation.json"):
        stage = f.name[: -len(".invocation.json")]
        try:
            out[stage] = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
    return out


# ============================================================
# CLI(skill/subagent/orchestrator 跑完调用)
# ============================================================

def main() -> int:
    ap = argparse.ArgumentParser(description="W4 invocation log 生产者 + 校验器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write", help="写一个 <stage>.invocation.json")
    w.add_argument("--slug", required=True)
    w.add_argument("--stage", required=True)
    w.add_argument("--skill", required=True, dest="skill_name")
    w.add_argument("--version", default="v1")
    w.add_argument("--round", type=int, default=1)
    g = w.add_mutually_exclusive_group(required=True)
    g.add_argument("--input-file", help="对该文件内容取 sha256 作 input_hash")
    g.add_argument("--input-hash", help="直接给 sha256:<hex>")
    w.add_argument("--output", nargs="*", default=[], dest="output_files")
    w.add_argument("--result", required=True)
    w.add_argument("--summary", default="")

    v = sub.add_parser("validate", help="校验一个 invocation.json 文件")
    v.add_argument("path")

    args = ap.parse_args()

    if args.cmd == "write":
        input_hash = args.input_hash or hash_file(args.input_file)
        path = write_invocation(
            slug=args.slug, stage=args.stage, skill_name=args.skill_name,
            version=args.version, round=args.round, input_hash=input_hash,
            output_files=args.output_files, result=args.result, summary=args.summary,
        )
        print(f"✅ 写入 {path}")
        return 0

    if args.cmd == "validate":
        obj = json.loads(Path(args.path).read_text(encoding="utf-8"))
        ok, errs = validate_invocation(obj)
        if ok:
            print(f"✅ {args.path} schema 合法")
            return 0
        print(f"❌ {args.path} schema 不合法:", file=sys.stderr)
        for e in errs:
            print(f"   - {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
