"""
test_opening_signal_cli.py — opening_signal CLI + W9 维度重校单测

W6: argparse CLI I/O 层(--trial 直读 / --draft 抽 intro → score_opening_signal → JSON)。
W9: 砍 反差感/具体性/信息密度 + 拆情绪锚点(留第一人称密度)+ 真首段字数 ≥50→≥25 +
     修字段名歧义(首段 = 真·首段,不是整个 intro 块)。本组测试断言 post-W9 行为。
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

from opening_signal import main, score_opening_signal  # noqa: E402

_TRIAL = (
    "前几天晚上,我看到一条消息。Anthropic 完成 300 亿美元融资,估值 9000 亿,反超 OpenAI。"
    "我把这两个数字念了一遍,又念了一遍。第一反应是,这跟我有什么关系。"
)


def test_main_trial_post_w9_shape(tmp_path, capsys):
    """W9: 返回保留 公式新鲜度 + 第一人称密度 + 物理;砍掉的 4 维不再出现."""
    trial = tmp_path / "opening_trial.txt"
    trial.write_text(_TRIAL, encoding="utf-8")
    rc = main(["--trial", str(trial)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    # 保留
    assert "verdict" in out and "physical_pass" in out
    assert "formula_freshness" in out
    assert "first_person_density" in out
    assert "first_para_chars" in out
    # W9 砍掉的 4 维不再出现在返回里
    for cut in ("concreteness", "reframe", "info_density", "emotion_anchor"):
        assert cut not in out, f"{cut} 应已被 W9 砍掉"


def test_cli_trial_matches_function(tmp_path, capsys):
    trial = tmp_path / "opening_trial.txt"
    trial.write_text(_TRIAL, encoding="utf-8")
    main(["--trial", str(trial)])
    via_cli = json.loads(capsys.readouterr().out)
    via_fn = score_opening_signal(trial.read_text(encoding="utf-8"))
    assert via_cli == via_fn


def test_main_draft_extracts_intro(tmp_path, capsys):
    """--draft:剥 frontmatter + 取第一个 \\n## 前作 intro."""
    draft = tmp_path / "20260527-test-v0.md"
    draft.write_text(
        f"---\ntitle: 测试\nauthor: 研究Agent的云\n---\n\n{_TRIAL}\n\n## 正文\n\n正文段落。\n",
        encoding="utf-8",
    )
    rc = main(["--draft", str(draft)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)

    raw = draft.read_text(encoding="utf-8")
    body = raw.split("---", 2)[2]
    m = re.search(r"\n##\s", body)
    intro = (body[:m.start()] if m else body).strip()
    assert out == score_opening_signal(intro)


def test_true_first_para_not_whole_intro_block(tmp_path):
    """W9 修字段名歧义:首段字数 = 真·首段(首个空行分隔块),不是整个 intro 块."""
    # intro 块多段:真·首段只有「我停了一下。」6 字,后面一长段不该计进首段
    intro = "我停了一下。\n\n" + "这后面是很长的第二段," * 10
    r = score_opening_signal(intro)
    assert r["first_para_chars"] == len(re.sub(r"\s+", "", "我停了一下。")), \
        "first_para_chars 应只数真·首段,不是整个 intro 块"


def test_first_para_threshold_is_25(tmp_path):
    """W9: 真首段字数阈值 50→25 —— 28 字第一人称首段物理通过(旧 50 阈值会卡)."""
    # 28 字、含多个第一人称 → 第一人称密度足够 + 真首段 ≥ 25
    intro = "我昨天又改了一版我自己的方案,我盯着屏幕看了很久才动手。"
    r = score_opening_signal(intro)
    assert 25 <= r["first_para_chars"] < 50
    # 28 字真首段 + 高第一人称密度 → 物理通过(旧 ≥50 阈值会卡;无「首段字数 <」类 fail)
    assert r["physical_pass"] is True
    assert not any("首段" in f for f in r.get("redo_feedback", "").split(" | ") if "<" in f)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
