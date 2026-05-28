"""
gate.py — Round 17 P0:Step 8 推草稿前的物理保安。

由 PreToolUse hook 触发(Claude 想跑 post_fengyun_publish.py 时),
+ post_fengyun_publish.py main() 第一行调用兜底。

行为:
  - 读 draft frontmatter,检查 WRITE_AGENT.md 定义的 11 个必填 pass_flag
  - 检查 cover_path + image_paths 文件物理存在
  - 缺一 → sys.exit(2) + 把 missing 列表打到 stderr
  - 全通过 → exit 0

Escape hatch:--force-skip-gate(只允许风云本人显式传,会留 audit 日志)

宪法依据:D:\\Dev\\ai-wechat-pipeline\\WRITE_AGENT.md
"""
from __future__ import annotations
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
AUDIT_LOG = ROOT / "output" / "runs" / "gate_audit.jsonl"

# W4: invocation log 消费。tools/ 入 sys.path,兼容 `python tools/gate.py` 与 pytest import。
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
import invocation_log as ilog  # noqa: E402


# ============================================================
# 必填 pass_flag 清单(WRITE_AGENT.md Step 8 定义)
# ============================================================

# 必填字段(基础 frontmatter,truthy 即可)
REQUIRED_BASE_FIELDS = ["title", "digest", "author", "slug", "date", "north_star"]

# ============================================================
# W4(2026-05-27,arch-refactor-v1):pipeline-state 防伪字段迁到 invocation log
# ============================================================
# 删 REQUIRED_PASS_FLAGS / REQUIRED_AUDIT_FIELDS / REQUIRED_SKILL_AUDIT_FIELDS /
# REQUIRED_SOURCE_PATTERNS / REQUIRED_EVIDENCE_FIELDS —— 这些 *_pass / *_real_run /
# *_source 是 hypothesis-non-fingo 材料(invariant #3),且证明不了「评的是最终稿」。
# 改由 output/runs/<slug>/<stage>.invocation.json 承载;gate 检查见 check_invocations()。
# 反 fake 升级(Newton 真 invariant):input_hash == sha256(当前 draft) 证明这一轨跑的是这一版。

# gate 推草稿前必须齐全的 invocation(pre-publish 6 件;
# render 由 Stop hook ship_complete_check.py 查)
REQUIRED_INVOCATIONS = [
    ("iti", "Stage 1 Collect — ITI 调研"),
    ("writer", "Stage 2 Write — fengyun-writer 出稿 + 标题/结尾 harness"),
    ("verify", "Stage 3 Verify — lint + 王小波 + 双轨 critic vote 决议"),
    ("critic_b_huashu", "Stage 3 Track B — huashu-perspective 灵魂"),
    ("critic_c_content_judge", "Stage 3 Track C — content-judge 挂名意愿"),
    ("cover", "Stage 4 Publish — 封面 + 花叔 Mode 2 配图"),
]

# 只对「操作最终稿」的 stage 强制 input_hash == sha256(当前 draft);
# iti/writer 的 input 是 research/前一版,不强制等于当前稿。
FINAL_DRAFT_STAGES = {"verify", "critic_b_huashu", "critic_c_content_judge", "cover"}

# verify.invocation.json 的 result 必须 ∈ 这些值才放行(force_ship = 隐藏天花板强制 ship)。
SHIP_DECISIONS = {"ship", "force_ship"}

# 必填文件路径(string,需检查物理存在)—— 物理产物指针,留 frontmatter(spec §1.1)
REQUIRED_FILE_FIELDS = [
    ("cover_path", "Step 7-cover 封面文件"),
]

# Round 25(2026-05-25 文内图强制必选,Musk × Newton 同意,Jobs 保留意见)
# 用户决策方案 A:image_paths 物理硬约束非空,删 should_illustrate=false 路径
# Newton 补丁:文件 size ≥ 5 KB(防全黑 / 报错图 / 0 字节通过)
# Musk 补丁:placeholder 是合法路径(daily_quota fallback),但 0 图绝对禁止
REQUIRED_IMAGE_PATHS_FIELD = "image_paths"   # 旧名 OPTIONAL_,Round 25 改强制
IMAGE_MIN_SIZE_BYTES = 5 * 1024  # 5 KB,Newton 有效性 floor
# Round 25 placeholder 路径(daily_quota fallback 合法,但 image_paths 仍要包含它)
PLACEHOLDER_IMAGE_PATH = "assets/placeholder-sketch.png"


# ============================================================
# Frontmatter 解析
# ============================================================

def parse_frontmatter(draft_path: Path) -> dict | None:
    """简易 YAML frontmatter 解析(不依赖 PyYAML).

    返回 dict 或 None(没有 frontmatter)。
    """
    if not draft_path.exists():
        return None
    text = draft_path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm_text = parts[1]
    fm: dict = {}
    # Round 21 P0-16:state machine 支持多行 YAML list
    # 当 val 为空且后续行以「  - 」开头时,聚合成 list
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line or line.startswith("#"):
            i += 1
            continue
        # 多行 list item 行(出现在某 key 之后,这里跳过 — 由上一轮处理)
        if line.lstrip().startswith("- "):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        # 简化 bool 解析
        if val.lower() in ("true", "yes"):
            fm[key] = True
        elif val.lower() in ("false", "no"):
            fm[key] = False
        elif val.startswith("[") and val.endswith("]"):
            # 简易 inline JSON list 解析
            inner = val[1:-1].strip()
            if inner:
                items = [x.strip().strip('"').strip("'") for x in inner.split(",")]
                try:
                    fm[key] = [int(x) for x in items]
                except ValueError:
                    fm[key] = items
            else:
                fm[key] = []
        elif val == "":
            # 可能是多行 YAML list 的 header,看后续行
            list_items = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j].rstrip()
                if not nxt or nxt.startswith("#"):
                    j += 1
                    continue
                stripped = nxt.lstrip()
                if stripped.startswith("- "):
                    item = stripped[2:].strip().strip('"').strip("'")
                    list_items.append(item)
                    j += 1
                else:
                    break
            if list_items:
                # 尝试转 int(image_at_h2_indices 这种)
                try:
                    fm[key] = [int(x) for x in list_items]
                except ValueError:
                    fm[key] = list_items
                i = j
                continue
            else:
                fm[key] = ""
        else:
            fm[key] = val
        i += 1
    return fm


# ============================================================
# 检查逻辑
# ============================================================

def check_draft(draft_path: Path) -> tuple[bool, list[str]]:
    """检查 draft frontmatter + 文件存在性.

    返回 (passed: bool, missing_reasons: list[str])
    """
    fm = parse_frontmatter(draft_path)
    if fm is None:
        return False, [f"draft 文件无法解析 frontmatter: {draft_path}"]

    missing: list[str] = []

    # 检查基础字段
    for field in REQUIRED_BASE_FIELDS:
        if not fm.get(field):
            missing.append(f"基础字段缺失:{field}(必填)")

    # W4: pass_flag 防伪检查已迁到 invocation log → 见函数末尾 check_invocations()

    # 检查文件路径字段(物理产物指针,留 frontmatter — spec §1.1)
    for field, file_desc in REQUIRED_FILE_FIELDS:
        path_str = fm.get(field)
        if not path_str:
            missing.append(f"缺路径字段:{field}={file_desc}")
            continue
        # path_str 可能是相对 ROOT 或绝对
        p = Path(path_str)
        if not p.is_absolute():
            p = ROOT / path_str
        if not p.exists():
            missing.append(f"{file_desc} 文件不存在:{p}")

    # Round 25 P0 文内图强制必选(用户方案 A · Musk × Newton 同意)
    # 物理硬约束:image_paths 必填非空 + 每个文件物理存在 + size ≥ 5 KB
    # 删除「image_at_h2_indices 空 list 也算 pass」的逃逸路径
    if "image_at_h2_indices" not in fm:
        missing.append("缺 image_at_h2_indices(Step 7.2 产物,Round 25 必填)")

    image_paths = fm.get(REQUIRED_IMAGE_PATHS_FIELD)
    if not image_paths:
        missing.append("image_paths 缺失或空 — 任何 ship 必须有 ≥ 1 张内文图")
    elif not isinstance(image_paths, list):
        missing.append(f"image_paths 字段类型应为 list,实际:{type(image_paths).__name__}")
    else:
        for ip in image_paths:
            p = Path(ip) if Path(ip).is_absolute() else ROOT / ip
            if not p.exists():
                missing.append(f"内文图文件不存在:{p}")
                continue
            try:
                size = p.stat().st_size
                if size < IMAGE_MIN_SIZE_BYTES:
                    missing.append(
                        f"内文图 size {size} bytes < {IMAGE_MIN_SIZE_BYTES} bytes 下限:{p}"
                    )
            except Exception as e:
                missing.append(f"内文图 stat 失败 {p}: {e}")

    # image_generation_degraded=true 路径已废弃(Round 25),仍写入会被 BLOCK
    if fm.get("image_generation_degraded") is True:
        missing.append("image_generation_degraded=true 已废弃(Round 25),应走 placeholder fallback")

    # W4: 配图决策 / critic 双轨 / writer-title-ending-王小波 的 fake-pass 防伪检查
    # 全部迁到 invocation log(cover.invocation.json / critic_b_huashu / critic_c_content_judge /
    # writer / verify)。见函数末尾 check_invocations()。

    # R18 字段 check(简易)— 留 frontmatter(物理红线状态)
    if fm.get("aborted_r18") is True:
        missing.append("⛔ R18 P0 已 abort,严禁推草稿 — 必须人工修后重跑全流程")

    # W4: pipeline-state 防伪 → invocation log。gate 查 invocation 集(取代旧 *_pass/*_real_run/*_source)
    missing.extend(check_invocations(fm.get("slug"), draft_path))

    passed = len(missing) == 0
    return passed, missing


def check_invocations(slug, draft_path: Path) -> list[str]:
    """W4:核验 output/runs/<slug>/ 下 6 个 pre-publish invocation 齐全且可信。

    每件:存在 + schema 合法 + finished_at < 1h;
    操作最终稿的 stage(verify/critic_b/critic_c/cover)额外要 input_hash == sha256(当前 draft);
    verify.result 必须 ∈ {ship, force_ship}(critic vote 决议)。
    """
    missing: list[str] = []
    if not slug:
        return ["缺 slug,无法定位 invocation log(output/runs/<slug>/)"]

    run = ilog.load_run(str(slug))
    for stage, desc in REQUIRED_INVOCATIONS:
        obj = run.get(stage)
        if obj is None:
            missing.append(f"缺 invocation:{stage}.invocation.json({desc})")
            continue
        ok, errs = ilog.validate_invocation(obj)
        if not ok:
            missing.append(f"{stage}.invocation.json schema 不合法:{errs[:3]}")
            continue
        if not ilog.is_fresh(obj):
            missing.append(
                f"{stage}.invocation.json 已过期(finished_at 距今 ≥ 1h)— 必须重跑该 stage"
            )
        if stage in FINAL_DRAFT_STAGES and not ilog.hash_matches(obj, draft_path):
            missing.append(
                f"⚠️ {stage}.invocation.json input_hash 不匹配当前 draft — "
                f"该 stage 跑的不是这一版稿(防 fake:不许拿旧版 verdict ship 新稿)"
            )

    # verify 决议必须是 ship / force_ship 才放行
    verify = run.get("verify")
    if verify is not None:
        result = str(verify.get("result", ""))
        if result not in SHIP_DECISIONS:
            missing.append(
                f"⛔ verify.invocation.json result={result!r} 不在 {sorted(SHIP_DECISIONS)} — "
                f"critic vote 未判 ship/force_ship,不许推草稿"
            )
    return missing


# ============================================================
# Audit log
# ============================================================

def write_audit_log(draft_path: Path, passed: bool, missing: list[str], force_skip: bool = False) -> None:
    """每次 gate 调用追加一行 audit log."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now().isoformat(),
        "draft": str(draft_path),
        "passed": passed,
        "missing_count": len(missing),
        "missing": missing[:10],  # 最多 10 条避免日志爆炸
        "force_skip": force_skip,
    }
    try:
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # audit log 写失败不阻断 gate
        pass


# ============================================================
# 从 hook 调用解析 draft path
# ============================================================

def extract_draft_path_from_args(argv: list[str]) -> Path | None:
    """从命令行参数里找 .md 文件(支持 hook 传参 + CLI 直接传)."""
    for a in argv:
        if a.endswith(".md") and "drafts" in a.replace("\\", "/"):
            p = Path(a)
            if not p.is_absolute():
                p = ROOT / a
            return p
    return None


def extract_from_stdin_hook_payload() -> tuple[Path | None, bool]:
    """Claude Code hook 通过 stdin 传 JSON payload.

    返回 (draft_path, is_publish_command)
      - is_publish_command=False 时 gate 放行(非 ship 场景)
      - is_publish_command=True 时必须 check
    """
    try:
        if sys.stdin.isatty():
            return None, False
        payload_str = sys.stdin.read()
        if not payload_str.strip():
            return None, False
        payload = json.loads(payload_str)
        cmd = (
            payload.get("tool_input", {}).get("command")
            or payload.get("command")
            or ""
        )
        # 关键 dispatcher:只在命令含 post_fengyun_publish 时才需要 check
        is_publish = "post_fengyun_publish" in cmd
        if not is_publish:
            return None, False
        # 匹配 .md path
        m = re.search(r"([A-Za-z]:[\\/][^\s]+\.md|output[\\/]drafts[\\/][^\s]+\.md)", cmd)
        if m:
            path_str = m.group(1)
            p = Path(path_str)
            if not p.is_absolute():
                p = ROOT / path_str
            return p, True
        return None, True  # 是 publish 命令但没找到 .md → 当作出错,继续走 check 流程
    except Exception:
        return None, False


# ============================================================
# CLI 主入口
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="Round 17 P0 — ship pipeline 物理保安")
    parser.add_argument("draft", nargs="?", help="draft markdown 路径(可选,会尝试从 stdin/argv 推断)")
    parser.add_argument("--force-skip-gate", action="store_true",
                        help="紧急绕过(只允许风云本人显式传,留 audit)")
    parser.add_argument("--check-only", action="store_true",
                        help="不退出,只打印检查结果(测试用)")
    args = parser.parse_args()

    # 推断 draft 路径
    draft_path = None
    is_publish_cmd = bool(args.draft)  # CLI 直接传 = 显式 check
    if args.draft:
        p = Path(args.draft)
        draft_path = p if p.is_absolute() else ROOT / args.draft
    if draft_path is None:
        draft_path, hook_is_publish = extract_from_stdin_hook_payload()
        is_publish_cmd = is_publish_cmd or hook_is_publish
    if draft_path is None:
        draft_path = extract_draft_path_from_args(sys.argv[1:])
        # CLI 含 .md path → 当作显式 check
        if draft_path:
            is_publish_cmd = True

    # 非 publish 命令 → 直接放行(只在 ship 时拦)
    if not is_publish_cmd:
        return 0

    if draft_path is None:
        print("⚠️  gate.py 收到 publish 命令但找不到 draft 路径 — 放行(避免误伤)", file=sys.stderr)
        return 0

    # Force skip 路径(留 audit)
    # Round 24 P1-1(Jobs 视角):强化警报 — audit log Row 38 实测被触发但用户无感知。
    # 现在用 9 行红框 + 收集当前 frontmatter 缺失字段一并记录,让 force_skip 不再静默
    if args.force_skip_gate:
        # 先跑一次 check_draft 拿到「本来会缺什么」— 即使 force-skip,也要记录绕过了哪些检查
        try:
            _passed_real, missing_real = check_draft(draft_path)
        except Exception as e:
            missing_real = [f"check_draft 异常: {e}"]
        write_audit_log(
            draft_path, passed=True,
            missing=["FORCE SKIP"] + [f"[bypassed] {m}" for m in missing_real[:10]],
            force_skip=True,
        )
        # 高亮红框警报 — Jobs 视角:让 force_skip 不再「静默走过去」
        print("", file=sys.stderr)
        print("╔══════════════════════════════════════════════════════════════════╗", file=sys.stderr)
        print("║  🚨 FORCE-SKIP-GATE 触发 — 本次 ship 走兜底通道,非正常 pass     ║", file=sys.stderr)
        print("╠══════════════════════════════════════════════════════════════════╣", file=sys.stderr)
        print(f"║  draft : {draft_path.name[:54]:<54}║", file=sys.stderr)
        print(f"║  绕过项: {len(missing_real)} 个 gate 检查 (详见 audit log)              ║", file=sys.stderr)
        print("║  含义  : 这次 ship 不是「真过」,是「被 --force-skip-gate 绕」    ║", file=sys.stderr)
        print("║  动作  : audit log 已写入 bypassed 字段,事后回查                ║", file=sys.stderr)
        print("╚══════════════════════════════════════════════════════════════════╝", file=sys.stderr)
        print("", file=sys.stderr)
        if missing_real:
            print(f"⚠️  被绕过的具体检查(前 5 条):", file=sys.stderr)
            for i, m in enumerate(missing_real[:5], 1):
                print(f"   [{i}] {m[:100]}", file=sys.stderr)
            print("", file=sys.stderr)
        return 0

    # 主检查
    passed, missing = check_draft(draft_path)
    write_audit_log(draft_path, passed, missing)

    if passed:
        print(f"✅ gate.py PASS:{draft_path.name} 所有 step 产物齐备,允许推草稿", file=sys.stderr)
        return 0

    # 失败 → 详细反馈
    print(f"❌ gate.py BLOCKED:{draft_path.name} 缺 {len(missing)} 个 step 产物", file=sys.stderr)
    print(f"   宪法依据:WRITE_AGENT.md", file=sys.stderr)
    print(f"", file=sys.stderr)
    for i, reason in enumerate(missing, 1):
        print(f"   [{i}] {reason}", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"主线程必须回去补完前置 step,再推草稿。", file=sys.stderr)
    print(f"紧急情况风云可显式传 --force-skip-gate(留 audit log)。", file=sys.stderr)

    if args.check_only:
        return 0
    return 2  # exit code 2 = PreToolUse hook 阻断 Claude


if __name__ == "__main__":
    sys.exit(main())
