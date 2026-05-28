"""
seedream_client.py — fengyun-publish 封面薄客户端(W7 cover 无模板重做)

迁自 generate_cover_by_template.py(2026-05-27 W7):
  - 常量 / load_dotenv / ARK 调用机制 / extract_title_subtitle / retry 结构 / sidecar 写出
    全部忠实迁移,**0 改业务逻辑**。

W7 的改动(只这几处,其余 0 改):
  1. prompt 透传:删 TEMPLATES[template_id] + .replace 模板,prompt 由花叔
     cover mode 写好后直接透传进 payload。无 TEMPLATES / classify / dedup。
  2. retry ×2 固定 2s → ×3 指数退避 1/2/4s(对齐 Round 25
     feedback_round25_image_mandatory),每次 retry 仍换随机 seed。
  3. 新增 placeholder fallback:全 retry 失败 → 复制 assets/placeholder-sketch.png
     到 out_path(Round 25 硬约束:image_paths 非空 + ≥ 5KB)。源缺失则 ok=False 不 crash。
  4. sidecar 去签名:anchor 从 style_anchor 入参写(不再硬编「soft cloud signature」);
     style_anchor 为 None 则不写 sidecar。

prompt 由 huashu-image-curator cover mode 写(无模板)。aspect 仅用于日志 +
让调用方知道,不进 payload(原代码 aspect 只在 prompt 文本里体现,payload 只发
size:"2K") —— 保留这个行为,不加 size-ratio 参数。

输入(CLI):
  --prompt <str>        必需 — 花叔 cover mode 写好的完整(中文)prompt,透传
  --aspect <str>        默认 "16:9" — 仅日志,不进 payload
  --out <path>          必需 — 输出 PNG 路径
  --title <str>         可选 — 仅元信息(prompt 内已含标题文字)
  --subtitle <str>      可选 — 仅元信息
  --seed <int>          可选 — 默认随机
  --style-anchor <str>  可选 — 非空则写 <out>.style_anchor.txt sidecar 供内文图复用
  --max-retries <int>   默认 3 — retry 次数(指数退避 sleep 序列 [1,2,4])

降级链:
  1. 豆包 Seedream(火山引擎方舟)— 主力 + retry ×3 指数退避
  2. 全失败 → placeholder fallback(assets/placeholder-sketch.png)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import ssl
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
load_dotenv(ROOT / ".env")

ARK_KEY = os.environ.get("VOLCENGINE_IMAGE_KEY")
ARK_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
MODEL = "doubao-seedream-5-0-260128"

# placeholder fallback 源(Round 25 硬约束:全失败时落这张保证 image_paths 非空 + ≥5KB)。
# 做成模块级常量,便于测试 monkeypatch 注入(不依赖真实 asset)。
PLACEHOLDER_SRC = ROOT / "assets" / "placeholder-sketch.png"

# retry 指数退避 sleep 序列(秒)。首次失败后 sleep 1s 重试,再失败 sleep 2s,再失败 sleep 4s。
BACKOFF_SECONDS = [1, 2, 4]


def extract_title_subtitle(draft_path):
    """从 draft frontmatter 抽 title / digest 作为副标。
    标题 > 14 字 → 13 + 「…」,副标 > 22 字 → 20 + 「…」(Seedream 渲染稳定性)。
    无 frontmatter title 时 fallback 第一个 H1。

    (忠实迁自 generate_cover_by_template.py:366-400,业务逻辑 0 改)
    """
    import re

    draft_path = Path(draft_path)
    text = draft_path.read_text(encoding="utf-8")
    title = ""
    digest = ""

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            for line in fm.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == "title" and not title:
                        title = v
                    elif k == "digest" and not digest:
                        digest = v

    # fallback:第一个 H1
    if not title:
        m = re.search(r"^#\s+(.+)$", text, flags=re.M)
        if m:
            title = m.group(1).strip()

    # 截断
    if len(title) > 14:
        title = title[:13] + "…"
    if len(digest) > 22:
        digest = digest[:20] + "…"

    return title, digest


def _call_seedream_once(prompt, out_path, seed=None):
    """单次调用 Seedream API,失败直接抛异常给上层 retry。

    迁自 generate_cover_by_template.py:406-445。
    W7 改动:prompt 直接透传进 payload(删 TEMPLATES[template_id] + .replace 那两行);
    size 固定 "2K"(原 tpl["size"] 全部模板都是 "2K")。其余 ARK HTTP 调用机制
    (urllib + ssl + payload + watermark:False + 下载图)0 改。
    """
    if not ARK_KEY:
        raise RuntimeError("VOLCENGINE_IMAGE_KEY 未在 .env 配置")

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": "2K",
        "response_format": "url",
        "watermark": False,
    }
    if seed is not None:
        payload["seed"] = int(seed)

    headers = {
        "Authorization": f"Bearer {ARK_KEY}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(
        ARK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    t0 = time.time()
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    img_url = data["data"][0]["url"]
    resp_seed = data["data"][0].get("seed")
    elapsed = time.time() - t0

    urllib.request.urlretrieve(img_url, str(out_path))
    return {"seed": resp_seed, "elapsed": elapsed, "url": img_url}


def _write_sidecar(out_path, style_anchor):
    """成功且 style_anchor 非空 → 写 <out>.style_anchor.txt sidecar 供内文图复用。

    迁自 generate_cover_by_template.py:631-637。
    W7 改动:anchor 内容从 style_anchor 入参写(不再硬编含「soft cloud signature」
    那段字符串);style_anchor 为 None / 空 → 不写。失败不阻断。
    """
    if not style_anchor:
        return None
    try:
        anchor_path = out_path.with_suffix(".style_anchor.txt")
        anchor_path.write_text(style_anchor, encoding="utf-8")
        print(f"style_anchor sidecar: {anchor_path}", flush=True)
        return anchor_path
    except Exception as _e:
        print(f"(style_anchor sidecar 写失败,不阻断: {_e})", flush=True)
        return None


def _placeholder_fallback(out_path):
    """全 retry 失败后复制 PLACEHOLDER_SRC 到 out_path(Round 25 硬约束)。
    返回 True 表示落盘成功;源文件不存在或复制失败返回 False(不 crash)。
    """
    import shutil

    if not PLACEHOLDER_SRC.exists():
        print(f"❌ placeholder 源文件不存在: {PLACEHOLDER_SRC}", flush=True)
        print(f"   (跑 assets/generate_placeholder.py 生成)", flush=True)
        return False
    try:
        out_path.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(str(PLACEHOLDER_SRC), str(out_path))
        print(f"🩹 placeholder fallback: {PLACEHOLDER_SRC} → {out_path}", flush=True)
        return True
    except Exception as e:
        print(f"❌ placeholder fallback 复制失败: {e}", flush=True)
        return False


def generate_cover(prompt, aspect, out_path, seed=None, style_anchor=None,
                   max_retries=3):
    """ARK Seedream 出图。prompt 透传(无模板)。

    retry × max_retries 指数退避(sleep 序列 [1,2,4])+ 每次换随机 seed。
    全失败 → placeholder fallback(assets/placeholder-sketch.png)。
    成功且 style_anchor 非空 → 写 <out>.style_anchor.txt sidecar(无签名)。

    Args:
        prompt: 花叔 cover mode 写好的完整 prompt(透传,不碰模板)。
        aspect: 仅用于日志 + 让调用方知道,不进 payload(prompt 文本里体现长宽比)。
        out_path: 输出 PNG 路径。
        seed: 初始 seed,None 则首次随机由 API 定。
        style_anchor: 非空则写 sidecar 供内文图复用(无云签名)。
        max_retries: retry 次数(默认 3),sleep 序列取 BACKOFF_SECONDS 前缀。

    Returns:
        dict: {ok, path, seed, placeholder_used, attempts, last_error?}
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(exist_ok=True, parents=True)

    print(f"[seedream] 调豆包 Seedream API (seed={seed or 'random'}, aspect={aspect})", flush=True)

    attempts = []
    last_error = None
    current_seed = seed

    for attempt_idx in range(max_retries + 1):
        try:
            r = _call_seedream_once(prompt, out_path, seed=current_seed)
            print(f"[seedream] OK (attempt {attempt_idx+1}, {r['elapsed']:.1f}s, seed={r['seed']})", flush=True)
            attempts.append({"attempt": attempt_idx + 1, "ok": True, "seed": r["seed"]})
            print(f"[seedream] ✓ {out_path.name}", flush=True)
            _write_sidecar(out_path, style_anchor)
            return {
                "ok": True,
                "path": str(out_path),
                "seed": r["seed"],
                "placeholder_used": False,
                "attempts": attempts,
            }
        except Exception as e:
            last_error = str(e)
            attempts.append({"attempt": attempt_idx + 1, "ok": False, "error": last_error,
                             "seed": current_seed})
            print(f"[seedream] ✗ attempt {attempt_idx+1} 失败: {last_error}", flush=True)
            if attempt_idx < max_retries:
                # 换 seed(保留原 L481 逻辑)
                current_seed = random.randint(1, 2**31 - 1)
                # 指数退避:第 attempt_idx 次失败后等 BACKOFF_SECONDS[attempt_idx]
                sleep_s = BACKOFF_SECONDS[attempt_idx] if attempt_idx < len(BACKOFF_SECONDS) else BACKOFF_SECONDS[-1]
                print(f"[seedream] ↻ retry,新 seed={current_seed},等待 {sleep_s}s", flush=True)
                time.sleep(sleep_s)

    # 全失败 → placeholder fallback(Round 25 硬约束)
    print(f"[seedream] ❌ 全部 {max_retries+1} 次失败", flush=True)
    print(f"  最后错误: {last_error}", flush=True)
    # 原 L488-489 手工提示保留为日志
    print(f"  建议:风云手工换 seed 或检查 prompt 后重跑", flush=True)

    if _placeholder_fallback(out_path):
        return {
            "ok": True,
            "path": str(out_path),
            "seed": None,
            "placeholder_used": True,
            "attempts": attempts,
            "last_error": last_error,
        }

    return {
        "ok": False,
        "path": None,
        "seed": None,
        "placeholder_used": False,
        "attempts": attempts,
        "last_error": last_error,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="seedream_client — 封面薄客户端(prompt 透传,无模板)"
    )
    parser.add_argument("--prompt", required=True,
                        help="花叔 cover mode 写好的完整 prompt(透传进 payload)")
    parser.add_argument("--aspect", default="16:9",
                        help="长宽比(仅日志,不进 payload;prompt 文本里体现)")
    parser.add_argument("--out", required=True, help="输出 PNG 路径")
    parser.add_argument("--title", default=None, help="标题(仅元信息,prompt 内已含)")
    parser.add_argument("--subtitle", default=None, help="副标(仅元信息)")
    parser.add_argument("--seed", type=int, default=None, help="指定 seed,不指定则随机")
    parser.add_argument("--style-anchor", default=None,
                        help="非空则写 <out>.style_anchor.txt sidecar 供内文图复用")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="retry 次数(默认 3,指数退避 sleep [1,2,4])")
    args = parser.parse_args(argv)

    out_path = Path(args.out)
    result = generate_cover(
        prompt=args.prompt,
        aspect=args.aspect,
        out_path=out_path,
        seed=args.seed,
        style_anchor=args.style_anchor,
        max_retries=args.max_retries,
    )
    if args.title is not None:
        result["title"] = args.title
    if args.subtitle is not None:
        result["subtitle"] = args.subtitle

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
